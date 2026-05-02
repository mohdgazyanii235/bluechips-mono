"""
Admin endpoints for verifying identities and managing escorts.
Protected by Admin JWT authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
import stripe

from app.database import get_db
from app.models.escort import Escort
from app.models.verification import Verification
from app.models.admin import Admin
from app.models.subscription import Subscription
from app.schemas.common import MessageResponse
from app.config import settings
from app.routers.deps import get_current_admin
from app.services.email_service import (
    send_verification_approved_to_escort,
    send_verification_denied_to_escort,
)
from app.services.storage_service import get_signed_url, delete_file
from app.utils.security import verify_password, create_access_token
from app.utils.rate_limit import is_rate_limited

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    email: str


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(data: AdminLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"admin_login:{client_ip}", max_attempts=5, window_seconds=900):
        raise HTTPException(status_code=429, detail="Too many login attempts. Please wait 15 minutes.")

    result = await db.execute(select(Admin).where(Admin.email == data.email.lower()))
    admin = result.scalar_one_or_none()
    if not admin or not verify_password(data.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account deactivated")
    token = create_access_token(str(admin.id))
    return AdminLoginResponse(access_token=token, email=admin.email)


@router.get("/stats")
async def admin_stats(admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    total_escorts = await db.scalar(select(func.count(Escort.id)))
    pending_verifications = await db.scalar(
        select(func.count(Verification.id)).where(Verification.status == "pending")
    )
    paid_escorts = await db.scalar(
        select(func.count(Escort.id)).where(Escort.subscription_tier != "free")
    )
    return {
        "total_escorts": total_escorts,
        "pending_verifications": pending_verifications,
        "paid_escorts": paid_escorts,
    }


class RejectVerificationRequest(BaseModel):
    admin_notes: str


@router.get("/verifications/pending")
async def pending_verifications(
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Verification)
        .options(selectinload(Verification.escort))
        .where(Verification.status == "pending")
        .order_by(Verification.submitted_at.desc())
    )
    items = result.scalars().all()
    return {
        "total": len(items),
        "items": [
            {
                "id": str(v.id),
                "escort_id": str(v.escort_id),
                "escort": {
                    "stage_name": v.escort.stage_name if v.escort else None,
                    "email": v.escort.email if v.escort else None,
                } if v.escort else None,
                "level": v.level,
                "level_name": "Identity Verification" if v.level == 2 else "Blue Tick",
                "submitted_at": v.submitted_at.isoformat(),
                "time_ago": _format_time_ago(v.submitted_at),
            }
            for v in items
        ],
    }


@router.get("/verifications/{verification_id}")
async def get_verification_detail(
    verification_id: str,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Verification)
        .options(selectinload(Verification.escort))
        .where(Verification.id == verification_id)
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")

    # Get signed URLs for documents (S3) or file paths (local)
    id_doc_signed = await get_signed_url(v.id_document_url) if v.id_document_url else None
    selfie_signed = await get_signed_url(v.selfie_url) if v.selfie_url else None
    match_selfie_signed = await get_signed_url(v.match_selfie_url) if v.match_selfie_url else None

    return {
        "id": str(v.id),
        "escort": {
            "id": str(v.escort.id),
            "stage_name": v.escort.stage_name,
            "email": v.escort.email,
            "subscription_tier": v.escort.subscription_tier,
            "subscription_expires_at": v.escort.subscription_expires_at.isoformat()
            if v.escort.subscription_expires_at
            else None,
        }
        if v.escort
        else None,
        "level": v.level,
        "level_name": "Identity Verification" if v.level == 2 else "Blue Tick",
        "status": v.status,
        "submitted_at": v.submitted_at.isoformat(),
        "reviewed_at": v.reviewed_at.isoformat() if v.reviewed_at else None,
        "admin_notes": v.admin_notes,
        "id_document_url": v.id_document_url,
        "id_document_signed_url": id_doc_signed,
        "selfie_url": v.selfie_url,
        "selfie_signed_url": selfie_signed,
        "match_selfie_url": v.match_selfie_url,
        "match_selfie_signed_url": match_selfie_signed,
    }


async def _cleanup_verification_docs(v: Verification) -> None:
    """Delete verification documents from storage immediately after admin decision."""
    for key in filter(None, [v.id_document_url, v.selfie_url, v.match_selfie_url]):
        try:
            await delete_file(key)
        except Exception as e:
            print(f"[CLEANUP] Could not delete verification doc {key}: {e}")
    v.id_document_url = None
    v.selfie_url = None
    v.match_selfie_url = None


@router.post("/verifications/{verification_id}/approve", response_model=MessageResponse)
async def approve_verification(
    verification_id: str,
    background_tasks: BackgroundTasks,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Verification)
        .options(selectinload(Verification.escort))
        .where(Verification.id == verification_id)
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")

    if v.status != "pending":
        raise HTTPException(status_code=400, detail="Can only approve pending verifications")

    v.status = "approved"
    v.reviewed_at = datetime.utcnow()
    v.reviewed_by = admin.email

    escort = v.escort

    if v.level == 2 and escort.subscription_tier in ["premium", "elite"]:
        # Premium/Elite: identity approval automatically grants Blue Tick too (included free)
        escort.verification_level = max(escort.verification_level, 3)
        escort.blue_tick_active = True
    elif v.level == 3:
        escort.verification_level = max(escort.verification_level, 3)
        escort.blue_tick_active = True
    else:
        escort.verification_level = max(escort.verification_level, v.level)

    await _cleanup_verification_docs(v)
    await db.flush()

    background_tasks.add_task(
        send_verification_approved_to_escort,
        escort_email=escort.email,
        escort_stage_name=escort.stage_name,
        level=v.level,
    )

    return MessageResponse(message="Verification approved. Escort notified.")


@router.post("/verifications/{verification_id}/reject", response_model=MessageResponse)
async def reject_verification(
    verification_id: str,
    body: RejectVerificationRequest,
    background_tasks: BackgroundTasks,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Verification)
        .options(selectinload(Verification.escort))
        .where(Verification.id == verification_id)
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Verification not found")

    if v.status != "pending":
        raise HTTPException(status_code=400, detail="Can only reject pending verifications")

    v.status = "rejected"
    v.reviewed_at = datetime.utcnow()
    v.reviewed_by = admin.email
    v.admin_notes = body.admin_notes

    escort = v.escort
    refund_error = None

    if v.level == 3:
        # Blue Tick rejection — cancel the Blue Tick subscription and refund its payment.
        # The main subscription (essential/premium/elite) is unaffected.
        if escort.blue_tick_stripe_subscription_id:
            try:
                invoices_result = stripe.Invoice.list(
                    subscription=escort.blue_tick_stripe_subscription_id,
                    api_key=settings.STRIPE_SECRET_KEY,
                    limit=1,
                )
                if invoices_result["data"]:
                    invoice = invoices_result["data"][0]
                    if invoice.get("charge"):
                        refund = stripe.Refund.create(
                            charge=invoice["charge"],
                            api_key=settings.STRIPE_SECRET_KEY,
                        )
                        v.refund_id = refund.id
                        v.refunded_at = datetime.utcnow()

                stripe.Subscription.delete(
                    escort.blue_tick_stripe_subscription_id,
                    api_key=settings.STRIPE_SECRET_KEY,
                )
            except stripe.error.StripeError as e:
                refund_error = str(e)
                print(f"[STRIPE ERROR] Blue Tick refund/cancel failed for {verification_id}: {e}")

            escort.blue_tick_active = False
            escort.blue_tick_stripe_subscription_id = None
            if escort.verification_level >= 3:
                escort.verification_level = 2

    elif v.level == 2:
        # Identity verification rejection — cancel the main subscription and refund it.
        if escort.subscription_tier in ["essential", "premium", "elite"]:
            try:
                if escort.stripe_subscription_id:
                    invoices_result = stripe.Invoice.list(
                        subscription=escort.stripe_subscription_id,
                        api_key=settings.STRIPE_SECRET_KEY,
                        limit=1,
                    )
                    if invoices_result["data"]:
                        invoice = invoices_result["data"][0]
                        if invoice.get("charge"):
                            refund = stripe.Refund.create(
                                charge=invoice["charge"],
                                api_key=settings.STRIPE_SECRET_KEY,
                            )
                            v.refund_id = refund.id
                            v.refunded_at = datetime.utcnow()

                    stripe.Subscription.delete(
                        escort.stripe_subscription_id,
                        api_key=settings.STRIPE_SECRET_KEY,
                    )
                    escort.stripe_subscription_id = None

                escort.subscription_tier = "free"
                if escort.verification_level == 2:
                    escort.verification_level = 1

            except stripe.error.StripeError as e:
                refund_error = str(e)
                print(f"[STRIPE ERROR] Identity refund/cancel failed for {verification_id}: {e}")

    await _cleanup_verification_docs(v)
    await db.flush()

    # Queue denial email
    background_tasks.add_task(
        send_verification_denied_to_escort,
        escort_email=escort.email,
        escort_stage_name=escort.stage_name,
        admin_notes=body.admin_notes,
        level=v.level,
    )

    if refund_error:
        return MessageResponse(
            message=f"Verification rejected. Escort notified. Note: Refund processing encountered an issue: {refund_error}"
        )
    return MessageResponse(message="Verification rejected. Escort notified and payment refunded.")


@router.get("/escorts")
async def list_all_escorts(
    page: int = 1,
    per_page: int = 50,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Escort)
        .order_by(Escort.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    escorts = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "stage_name": e.stage_name,
            "email": e.email,
            "subscription_tier": e.subscription_tier,
            "verification_level": e.verification_level,
            "is_active": e.is_active,
            "is_approved": e.is_approved,
            "is_email_verified": e.is_email_verified,
            "created_at": e.created_at,
        }
        for e in escorts
    ]


@router.patch("/escorts/{escort_id}/toggle-active", response_model=MessageResponse)
async def toggle_escort_active(
    escort_id: str,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Escort).where(Escort.id == escort_id))
    escort = result.scalar_one_or_none()
    if not escort:
        raise HTTPException(status_code=404, detail="Escort not found")
    escort.is_active = not escort.is_active
    await db.flush()
    return MessageResponse(message=f"Escort {'activated' if escort.is_active else 'deactivated'}")


def _format_time_ago(dt: datetime) -> str:
    """Format a datetime as a relative string like '5 minutes ago'"""
    now = datetime.utcnow()
    delta = now - dt

    seconds = delta.total_seconds()
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
