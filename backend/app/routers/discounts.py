from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.discount import DiscountCode
from app.models.escort import Escort
from app.routers.deps import get_current_verified_escort

router = APIRouter(tags=["Discounts"])

TIER_MONTHLY_PRICE_PENCE = {
    "essential": 2499,
    "premium": 4999,
    "elite": 8999,
    "blue_tick": 399,
}
TIER_ANNUAL_PRICE_PENCE = {
    "essential": 24990,
    "premium": 49990,
    "elite": 89990,
}


class ValidateCodeRequest(BaseModel):
    code: str
    tier: str
    billing: str = "monthly"


class ValidateCodeResponse(BaseModel):
    valid: bool
    code_type: Optional[str] = None  # "discount" | "referral"
    percent_off: Optional[int] = None
    duration_months: Optional[int] = None
    discount_amount_pence: Optional[int] = None
    message: Optional[str] = None


def _calc_discount_pence(tier: str, billing: str, percent_off: int, duration_months: int) -> int:
    if billing == "annual" and tier in TIER_ANNUAL_PRICE_PENCE:
        return int((TIER_ANNUAL_PRICE_PENCE[tier] / 12) * (percent_off / 100) * duration_months)
    monthly = TIER_MONTHLY_PRICE_PENCE.get(tier, 0)
    return int(monthly * (percent_off / 100) * duration_months)


@router.post("/discounts/validate", response_model=ValidateCodeResponse)
async def validate_code(
    body: ValidateCodeRequest,
    escort: Escort = Depends(get_current_verified_escort),
    db: AsyncSession = Depends(get_db),
):
    code = body.code.strip().upper()

    # 1 — check admin discount codes first
    result = await db.execute(
        select(DiscountCode).where(
            DiscountCode.code == code,
            DiscountCode.is_active == True,
        )
    )
    discount = result.scalar_one_or_none()

    if discount:
        if discount.max_redemptions is not None and discount.current_redemptions >= discount.max_redemptions:
            return ValidateCodeResponse(valid=False, message="This code has reached its maximum number of uses")
        if discount.applicable_tiers and body.tier not in discount.applicable_tiers:
            names = ", ".join(t.title() for t in discount.applicable_tiers)
            return ValidateCodeResponse(valid=False, message=f"This code is only valid for: {names}")
        return ValidateCodeResponse(
            valid=True,
            code_type="discount",
            percent_off=discount.percent_off,
            duration_months=discount.duration_months,
            discount_amount_pence=_calc_discount_pence(body.tier, body.billing, discount.percent_off, discount.duration_months),
        )

    # 2 — check referral codes
    ref_result = await db.execute(
        select(Escort).where(Escort.referral_code == code)
    )
    referrer = ref_result.scalar_one_or_none()

    if referrer:
        if referrer.id == escort.id:
            return ValidateCodeResponse(valid=False, message="You cannot use your own referral code")
        return ValidateCodeResponse(
            valid=True,
            code_type="referral",
            percent_off=50,
            duration_months=3,
            discount_amount_pence=_calc_discount_pence(body.tier, body.billing, 50, 3),
        )

    return ValidateCodeResponse(valid=False, message="Code not found or no longer active")
