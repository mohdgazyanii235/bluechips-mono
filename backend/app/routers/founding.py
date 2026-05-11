"""
Founding offer endpoints — admin config + public counter for the landing page.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.admin import Admin
from app.models.platform_config import PlatformConfig
from app.routers.deps import get_current_admin
from app.schemas.common import MessageResponse


router = APIRouter(tags=["Founding Offer"])

ALLOWED_TIERS = {"essential", "premium", "elite"}


# ─── Schemas ──────────────────────────────────────────────────────────────────


class FoundingOfferOut(BaseModel):
    active: bool
    limit: int
    signups: int
    remaining: int
    percent_off: int
    duration_months: int
    tier: str
    includes_blue_tick: bool
    lifetime_discount_percent: int
    badge_label: str


class FoundingOfferUpdate(BaseModel):
    active: Optional[bool] = None
    limit: Optional[int] = Field(None, ge=1, le=10000)
    signups: Optional[int] = Field(None, ge=0)
    percent_off: Optional[int] = Field(None, ge=1, le=100)
    duration_months: Optional[int] = Field(None, ge=1, le=24)
    tier: Optional[str] = None
    includes_blue_tick: Optional[bool] = None
    lifetime_discount_percent: Optional[int] = Field(None, ge=0, le=100)
    badge_label: Optional[str] = Field(None, max_length=50)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _serialize(cfg: PlatformConfig) -> dict:
    return {
        "active": cfg.founding_offer_active,
        "limit": cfg.founding_offer_limit,
        "signups": cfg.founding_offer_signups,
        "remaining": max(0, cfg.founding_offer_limit - cfg.founding_offer_signups),
        "percent_off": cfg.founding_offer_percent_off,
        "duration_months": cfg.founding_offer_duration_months,
        "tier": cfg.founding_offer_tier,
        "includes_blue_tick": cfg.founding_offer_includes_blue_tick,
        "lifetime_discount_percent": cfg.founding_offer_lifetime_discount_percent,
        "badge_label": cfg.founding_offer_badge_label,
    }


async def _get_config(db: AsyncSession) -> PlatformConfig:
    result = await db.execute(select(PlatformConfig).where(PlatformConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=500, detail="Platform config not initialised")
    return cfg


# ─── Public endpoint (for landing page counter) ───────────────────────────────


public_router = APIRouter(prefix="/founding", tags=["Founding Offer Public"])


@public_router.get("/status")
async def founding_offer_status(db: AsyncSession = Depends(get_db)):
    """Public, cached endpoint for the landing page counter."""
    cfg = await _get_config(db)
    return _serialize(cfg)


# ─── Admin endpoints ──────────────────────────────────────────────────────────


@router.get("/admin/founding-offer")
async def admin_get_founding_offer(
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    cfg = await _get_config(db)
    return _serialize(cfg)


@router.put("/admin/founding-offer", response_model=MessageResponse)
async def admin_update_founding_offer(
    body: FoundingOfferUpdate,
    admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    cfg = await _get_config(db)

    if body.active is not None:
        cfg.founding_offer_active = body.active
    if body.limit is not None:
        cfg.founding_offer_limit = body.limit
    if body.signups is not None:
        cfg.founding_offer_signups = body.signups
    if body.percent_off is not None:
        cfg.founding_offer_percent_off = body.percent_off
    if body.duration_months is not None:
        cfg.founding_offer_duration_months = body.duration_months
    if body.tier is not None:
        if body.tier not in ALLOWED_TIERS:
            raise HTTPException(status_code=400, detail=f"Tier must be one of: {', '.join(ALLOWED_TIERS)}")
        cfg.founding_offer_tier = body.tier
    if body.includes_blue_tick is not None:
        cfg.founding_offer_includes_blue_tick = body.includes_blue_tick
    if body.lifetime_discount_percent is not None:
        cfg.founding_offer_lifetime_discount_percent = body.lifetime_discount_percent
    if body.badge_label is not None:
        cfg.founding_offer_badge_label = body.badge_label.strip() or "Founding Member"

    cfg.updated_at = datetime.utcnow()
    cfg.updated_by = admin.email
    await db.flush()
    return MessageResponse(message="Founding offer updated")
