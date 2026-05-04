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
from app.models.discount import DiscountCode
from app.models.escort import Escort
from app.models.platform_config import PlatformConfig
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


# ── Discount Code Management ──────────────────────────────────────────────────

ALLOWED_TIERS = {"essential", "premium", "elite", "blue_tick"}


class CreateDiscountRequest(BaseModel):
    code: str
    name: str
    percent_off: int
    applicable_tiers: list[str] = []  # empty = all tiers
    duration_months: int
    max_redemptions: Optional[int] = None


@router.post("/discounts", response_model=MessageResponse)
async def create_discount_code(
    body: CreateDiscountRequest,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    code = body.code.strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    if not 1 <= body.percent_off <= 100:
        raise HTTPException(status_code=400, detail="percent_off must be 1–100")
    if body.duration_months < 1:
        raise HTTPException(status_code=400, detail="duration_months must be at least 1")
    if body.applicable_tiers and not set(body.applicable_tiers).issubset(ALLOWED_TIERS):
        raise HTTPException(status_code=400, detail=f"Invalid tiers. Allowed: {', '.join(ALLOWED_TIERS)}")

    existing = await db.execute(select(DiscountCode).where(DiscountCode.code == code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A discount code with this name already exists")

    dc = DiscountCode(
        code=code,
        name=body.name.strip(),
        percent_off=body.percent_off,
        applicable_tiers=body.applicable_tiers,
        duration_months=body.duration_months,
        max_redemptions=body.max_redemptions,
    )
    db.add(dc)
    await db.flush()
    return MessageResponse(message=f"Discount code '{code}' created successfully")


@router.get("/discounts")
async def list_discount_codes(
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DiscountCode).order_by(DiscountCode.created_at.desc())
    )
    codes = result.scalars().all()
    return [
        {
            "id": str(dc.id),
            "code": dc.code,
            "name": dc.name,
            "percent_off": dc.percent_off,
            "applicable_tiers": dc.applicable_tiers,
            "duration_months": dc.duration_months,
            "max_redemptions": dc.max_redemptions,
            "current_redemptions": dc.current_redemptions,
            "is_active": dc.is_active,
            "created_at": dc.created_at.isoformat(),
        }
        for dc in codes
    ]


@router.patch("/discounts/{code_id}/deactivate", response_model=MessageResponse)
async def deactivate_discount_code(
    code_id: str,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DiscountCode).where(DiscountCode.id == code_id))
    dc = result.scalar_one_or_none()
    if not dc:
        raise HTTPException(status_code=404, detail="Discount code not found")
    dc.is_active = False
    await db.flush()
    return MessageResponse(message=f"Discount code '{dc.code}' deactivated")


# ─── Pricing Management ───────────────────────────────────────────────────────

_PRICING_FIELDS = [
    ("essential_monthly_pence", "stripe_essential_monthly_id", "month", False),
    ("essential_annual_pence",  "stripe_essential_annual_id",  "year",  False),
    ("premium_monthly_pence",   "stripe_premium_monthly_id",   "month", False),
    ("premium_annual_pence",    "stripe_premium_annual_id",    "year",  False),
    ("elite_monthly_pence",     "stripe_elite_monthly_id",     "month", False),
    ("elite_annual_pence",      "stripe_elite_annual_id",      "year",  False),
    ("blue_tick_setup_pence",   "stripe_blue_tick_setup_id",   None,    True),
    ("blue_tick_monthly_pence", "stripe_blue_tick_monthly_id", "month", False),
]


class UpdatePricingRequest(BaseModel):
    essential_monthly_pence: Optional[int] = None
    essential_annual_pence: Optional[int] = None
    premium_monthly_pence: Optional[int] = None
    premium_annual_pence: Optional[int] = None
    elite_monthly_pence: Optional[int] = None
    elite_annual_pence: Optional[int] = None
    blue_tick_setup_pence: Optional[int] = None
    blue_tick_monthly_pence: Optional[int] = None


@router.get("/pricing")
async def get_pricing_config(admin: Admin = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PlatformConfig).where(PlatformConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=503, detail="Platform config not initialised — restart the server")

    price_fields = [f for f, _, _, _ in _PRICING_FIELDS]
    stripe_fields = [s for _, s, _, _ in _PRICING_FIELDS]
    return {
        **{f: getattr(cfg, f) for f in price_fields},
        **{s: getattr(cfg, s) for s in stripe_fields},
        "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None,
        "updated_by": cfg.updated_by,
    }


@router.put("/pricing", response_model=MessageResponse)
async def update_pricing(
    data: UpdatePricingRequest,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PlatformConfig).where(PlatformConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=503, detail="Platform config not initialised")

    stripe_client = None
    if settings.STRIPE_SECRET_KEY:
        stripe_client = stripe.StripeClient(settings.STRIPE_SECRET_KEY)

    for price_field, stripe_id_field, interval, is_one_time in _PRICING_FIELDS:
        new_amount = getattr(data, price_field)
        if new_amount is None:
            continue
        if new_amount < 1:
            raise HTTPException(status_code=400, detail=f"{price_field} must be at least 1 pence")

        current_amount = getattr(cfg, price_field)
        if new_amount == current_amount:
            continue

        # Create new Stripe price when amount changes and Stripe is configured
        if stripe_client:
            current_price_id = getattr(cfg, stripe_id_field, "")
            if current_price_id:
                try:
                    old_price = stripe_client.prices.retrieve(current_price_id)
                    product_id = old_price["product"]

                    price_params: dict = {
                        "unit_amount": new_amount,
                        "currency": "gbp",
                        "product": product_id,
                    }
                    if not is_one_time and interval:
                        price_params["recurring"] = {"interval": interval}

                    new_price = stripe_client.prices.create(params=price_params)
                    # Archive the old price so it no longer appears as active
                    stripe_client.prices.update(current_price_id, params={"active": False})
                    setattr(cfg, stripe_id_field, new_price.id)
                except Exception as e:
                    print(f"[STRIPE] Failed to create new price for {price_field}: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Stripe price creation failed for {price_field}. No changes saved.",
                    )

        setattr(cfg, price_field, new_amount)

    cfg.updated_at = datetime.utcnow()
    cfg.updated_by = admin.email
    await db.flush()
    return MessageResponse(message="Pricing updated successfully")
