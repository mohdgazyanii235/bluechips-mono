"""
Outreach CRM endpoints for tracking X DM outreach to companion prospects.
Protected by Admin JWT.
"""
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc, and_, or_
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.admin import Admin
from app.models.discount import DiscountCode
from app.models.escort import Escort
from app.models.outreach import OutreachProspect, ALLOWED_STATUSES, STATUS_CONTACTED
from app.models.platform_config import PlatformConfig
from app.routers.deps import get_current_admin
from app.schemas.common import MessageResponse
from app.services.email_service import send_profile_completion_reminder
from app.services.outreach_message import generate_message, OutreachContext

router = APIRouter(prefix="/admin/outreach", tags=["Admin Outreach"])


# ─── Schemas ──────────────────────────────────────────────────────────────────


class ProspectRow(BaseModel):
    """One editable row in the tabular UI — used for create + bulk upsert."""
    id: Optional[str] = None  # if set, update existing; if None, create new
    x_handle: str = Field(..., min_length=1, max_length=100)
    stage_name: str = Field(..., min_length=1, max_length=100)
    area: Optional[str] = Field(None, max_length=100)
    specialty: Optional[str] = Field(None, max_length=100)
    note: Optional[str] = None
    status: Optional[str] = None
    admin_notes: Optional[str] = None


class BulkUpsertRequest(BaseModel):
    rows: List[ProspectRow]


class UpdateProspectRequest(BaseModel):
    x_handle: Optional[str] = None
    stage_name: Optional[str] = None
    area: Optional[str] = None
    specialty: Optional[str] = None
    note: Optional[str] = None
    status: Optional[str] = None
    admin_notes: Optional[str] = None


class ProspectOut(BaseModel):
    id: str
    x_handle: str
    stage_name: str
    area: Optional[str]
    specialty: Optional[str]
    note: Optional[str]
    status: str
    generated_message: Optional[str]
    admin_notes: Optional[str]
    discount_code: Optional[str]
    discount_code_id: Optional[str]
    converted_escort_id: Optional[str]
    contacted_at: Optional[str]
    replied_at: Optional[str]
    signed_up_at: Optional[str]
    created_at: str
    updated_at: str


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _serialize(p: OutreachProspect, code: Optional[DiscountCode] = None) -> dict:
    return {
        "id": str(p.id),
        "x_handle": p.x_handle,
        "stage_name": p.stage_name,
        "area": p.area,
        "specialty": p.specialty,
        "note": p.note,
        "status": p.status,
        "generated_message": p.generated_message,
        "admin_notes": p.admin_notes,
        "discount_code": code.code if code else None,
        "discount_code_id": str(p.discount_code_id) if p.discount_code_id else None,
        "converted_escort_id": str(p.converted_escort_id) if p.converted_escort_id else None,
        "contacted_at": p.contacted_at.isoformat() if p.contacted_at else None,
        "replied_at": p.replied_at.isoformat() if p.replied_at else None,
        "signed_up_at": p.signed_up_at.isoformat() if p.signed_up_at else None,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


async def _unique_code(db: AsyncSession, handle: str, prefix: str = "FM") -> str:
    """Build a unique-yet-readable code for a prospect. Tries FM-HANDLE first, then falls back to random."""
    sanitized = "".join(c for c in (handle or "").upper() if c.isalnum())[:8]
    candidates = []
    if sanitized:
        candidates.append(f"{prefix}-{sanitized}")
    for _ in range(50):
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        candidates.append(f"{prefix}-{suffix}")

    for cand in candidates:
        existing = await db.execute(select(DiscountCode.id).where(DiscountCode.code == cand))
        if not existing.scalar_one_or_none():
            return cand
    raise RuntimeError("Could not generate a unique founding code")


async def _get_founding_config(db: AsyncSession) -> PlatformConfig:
    result = await db.execute(select(PlatformConfig).where(PlatformConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=500, detail="Platform config not initialised")
    return cfg


async def _ensure_discount_for_prospect(
    db: AsyncSession, prospect: OutreachProspect, cfg: PlatformConfig
) -> DiscountCode:
    """Ensure the prospect has an associated discount code. Reuse existing or create new."""
    if prospect.discount_code_id:
        existing = await db.execute(
            select(DiscountCode).where(DiscountCode.id == prospect.discount_code_id)
        )
        code = existing.scalar_one_or_none()
        if code:
            return code

    new_code_str = await _unique_code(db, prospect.x_handle)
    code = DiscountCode(
        code=new_code_str,
        name=f"Founding Member — {prospect.stage_name} (@{prospect.x_handle})",
        percent_off=cfg.founding_offer_percent_off,
        applicable_tiers=[],  # empty = valid for any paid tier
        duration_months=cfg.founding_offer_duration_months,
        max_redemptions=1,
        current_redemptions=0,
        is_active=True,
    )
    db.add(code)
    await db.flush()
    prospect.discount_code_id = code.id
    await db.flush()
    return code


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get("")
async def list_prospects(
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all outreach prospects with their associated discount codes."""
    result = await db.execute(
        select(OutreachProspect, DiscountCode)
        .outerjoin(DiscountCode, OutreachProspect.discount_code_id == DiscountCode.id)
        .order_by(OutreachProspect.created_at.desc())
    )
    rows = result.all()

    # Aggregate counts for funnel metrics
    counts = {s: 0 for s in ALLOWED_STATUSES}
    counts["total"] = 0
    items = []
    for prospect, code in rows:
        counts[prospect.status] = counts.get(prospect.status, 0) + 1
        counts["total"] += 1
        items.append(_serialize(prospect, code))

    return {"counts": counts, "items": items}


@router.post("/bulk-upsert")
async def bulk_upsert_prospects(
    body: BulkUpsertRequest,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a list of rows. For each row:
      - If id is set, update the existing record (only changed fields)
      - If id is None, create a new prospect (auto-generates a discount code)
    Returns the full updated/created records.
    """
    cfg = await _get_founding_config(db)
    created_count = 0
    updated_count = 0
    failures: List[dict] = []
    saved_ids: List[str] = []

    for row in body.rows:
        try:
            handle_clean = row.x_handle.strip().lstrip("@")
            if not handle_clean:
                failures.append({"x_handle": row.x_handle, "reason": "handle is empty"})
                continue

            if row.id:
                # Update existing
                existing = await db.execute(
                    select(OutreachProspect).where(OutreachProspect.id == row.id)
                )
                p = existing.scalar_one_or_none()
                if not p:
                    failures.append({"x_handle": row.x_handle, "reason": "id not found"})
                    continue
                # If handle changed, ensure uniqueness
                if handle_clean.lower() != p.x_handle.lower():
                    dup = await db.execute(
                        select(OutreachProspect.id).where(
                            sqlfunc.lower(OutreachProspect.x_handle) == handle_clean.lower(),
                            OutreachProspect.id != p.id,
                        )
                    )
                    if dup.scalar_one_or_none():
                        failures.append({"x_handle": row.x_handle, "reason": "handle already in use"})
                        continue
                p.x_handle = handle_clean
                p.stage_name = row.stage_name.strip()
                p.area = (row.area or "").strip() or None
                p.specialty = (row.specialty or "").strip() or None
                p.note = (row.note or "").strip() or None
                if row.status and row.status in ALLOWED_STATUSES:
                    p.status = row.status
                if row.admin_notes is not None:
                    p.admin_notes = row.admin_notes
                updated_count += 1
            else:
                # Insert new — first check the handle isn't a duplicate
                dup = await db.execute(
                    select(OutreachProspect.id).where(
                        sqlfunc.lower(OutreachProspect.x_handle) == handle_clean.lower()
                    )
                )
                if dup.scalar_one_or_none():
                    failures.append({"x_handle": row.x_handle, "reason": "handle already in list"})
                    continue
                p = OutreachProspect(
                    x_handle=handle_clean,
                    stage_name=row.stage_name.strip(),
                    area=(row.area or "").strip() or None,
                    specialty=(row.specialty or "").strip() or None,
                    note=(row.note or "").strip() or None,
                    status=row.status if row.status in ALLOWED_STATUSES else "not_contacted",
                    admin_notes=row.admin_notes,
                )
                db.add(p)
                await db.flush()
                # Auto-generate a discount code for new prospects
                await _ensure_discount_for_prospect(db, p, cfg)
                created_count += 1

            await db.flush()
            saved_ids.append(str(p.id))
        except Exception as e:  # pragma: no cover
            failures.append({"x_handle": row.x_handle, "reason": str(e)})

    return {
        "created": created_count,
        "updated": updated_count,
        "failures": failures,
        "saved_ids": saved_ids,
    }


@router.patch("/{prospect_id}", response_model=MessageResponse)
async def update_prospect(
    prospect_id: str,
    body: UpdateProspectRequest,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OutreachProspect).where(OutreachProspect.id == prospect_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    if body.x_handle is not None:
        p.x_handle = body.x_handle.strip().lstrip("@")
    if body.stage_name is not None:
        p.stage_name = body.stage_name.strip()
    if body.area is not None:
        p.area = body.area.strip() or None
    if body.specialty is not None:
        p.specialty = body.specialty.strip() or None
    if body.note is not None:
        p.note = body.note.strip() or None
    if body.admin_notes is not None:
        p.admin_notes = body.admin_notes
    if body.status is not None:
        if body.status not in ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {', '.join(ALLOWED_STATUSES)}")
        # Auto-set timestamps when status transitions
        if body.status == "contacted" and not p.contacted_at:
            p.contacted_at = datetime.utcnow()
        if body.status == "replied" and not p.replied_at:
            p.replied_at = datetime.utcnow()
        p.status = body.status

    await db.flush()
    return MessageResponse(message="Prospect updated")


@router.delete("/{prospect_id}", response_model=MessageResponse)
async def delete_prospect(
    prospect_id: str,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OutreachProspect).where(OutreachProspect.id == prospect_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")
    # Note: do NOT delete the discount code. The code lives independently and may have been used.
    await db.delete(p)
    return MessageResponse(message="Prospect deleted")


class GenerateMessageRequest(BaseModel):
    regenerate: bool = False  # if true, generate a different variant than what's stored


@router.post("/{prospect_id}/generate-message")
async def generate_prospect_message(
    prospect_id: str,
    body: GenerateMessageRequest = GenerateMessageRequest(),
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate (or regenerate) a personalised DM for a prospect. Returns the message text."""
    result = await db.execute(select(OutreachProspect).where(OutreachProspect.id == prospect_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")

    cfg = await _get_founding_config(db)
    code = await _ensure_discount_for_prospect(db, p, cfg)

    tier_label = (cfg.founding_offer_tier or "premium").title()
    tier_monthly_pence = {
        "essential": cfg.essential_monthly_pence,
        "premium": cfg.premium_monthly_pence,
        "elite": cfg.elite_monthly_pence,
    }.get(cfg.founding_offer_tier or "premium", cfg.premium_monthly_pence)

    ctx = OutreachContext(
        stage_name=p.stage_name,
        area=p.area,
        specialty=p.specialty,
        note=p.note,
        code=code.code,
        duration_months=cfg.founding_offer_duration_months,
        percent_off=cfg.founding_offer_percent_off,
        tier_label=tier_label,
        includes_blue_tick=cfg.founding_offer_includes_blue_tick,
        lifetime_discount_percent=cfg.founding_offer_lifetime_discount_percent,
        limit=cfg.founding_offer_limit,
        signups_so_far=cfg.founding_offer_signups,
    )

    # Use a regen counter so the same prospect can get a fresh variant on demand
    regenerate_token = 0
    if body.regenerate and p.generated_message:
        # Walk through the variants by hashing the existing message length
        regenerate_token = (len(p.generated_message) % 7) + 1

    message = generate_message(ctx, monthly_pence=tier_monthly_pence, regenerate_token=regenerate_token)
    p.generated_message = message
    await db.flush()

    return {"message": message, "code": code.code}


@router.post("/{prospect_id}/mark-contacted", response_model=MessageResponse)
async def mark_contacted(
    prospect_id: str,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OutreachProspect).where(OutreachProspect.id == prospect_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Prospect not found")
    p.status = STATUS_CONTACTED
    p.contacted_at = datetime.utcnow()
    await db.flush()
    return MessageResponse(message="Marked as contacted")


# ─── Email drip — profile completion reminder ────────────────────────────────


class DripPreviewItem(BaseModel):
    id: str
    email: str
    stage_name: str
    created_at: str


@router.get("/drip/profile-completion/preview")
async def preview_profile_completion_drip(
    days_old: int = 2,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns the list of escorts who would receive the completion-reminder email."""
    cutoff = datetime.utcnow() - timedelta(days=days_old)
    result = await db.execute(
        select(Escort).where(
            Escort.is_email_verified == True,
            Escort.profile_complete == False,
            Escort.is_active == True,
            Escort.created_at <= cutoff,
            or_(Escort.profile_reminder_sent_at.is_(None), Escort.profile_reminder_sent_at < cutoff),
        ).order_by(Escort.created_at.desc())
    )
    items = result.scalars().all()
    return {
        "count": len(items),
        "items": [
            {
                "id": str(e.id),
                "email": e.email,
                "stage_name": e.stage_name,
                "created_at": e.created_at.isoformat(),
                "last_reminded_at": e.profile_reminder_sent_at.isoformat() if e.profile_reminder_sent_at else None,
            }
            for e in items
        ],
    }


@router.post("/drip/profile-completion/send")
async def send_profile_completion_drip(
    background_tasks: BackgroundTasks,
    days_old: int = 2,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Triggers the completion-reminder email for all eligible escorts. Safe to call repeatedly — won't double-send within `days_old` days."""
    cutoff = datetime.utcnow() - timedelta(days=days_old)
    result = await db.execute(
        select(Escort).where(
            Escort.is_email_verified == True,
            Escort.profile_complete == False,
            Escort.is_active == True,
            Escort.created_at <= cutoff,
            or_(Escort.profile_reminder_sent_at.is_(None), Escort.profile_reminder_sent_at < cutoff),
        )
    )
    eligible = result.scalars().all()
    now = datetime.utcnow()
    queued = 0
    for escort in eligible:
        background_tasks.add_task(send_profile_completion_reminder, escort.email, escort.stage_name)
        escort.profile_reminder_sent_at = now
        queued += 1
    await db.flush()
    return {"queued": queued, "message": f"Queued {queued} reminder email(s)"}
