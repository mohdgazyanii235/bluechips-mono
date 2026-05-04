from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.platform_config import PlatformConfig

router = APIRouter(tags=["Pricing"])


@router.get("/pricing")
async def get_pricing(db: AsyncSession = Depends(get_db)):
    """Public endpoint — returns current tier prices for frontend display."""
    result = await db.execute(select(PlatformConfig).where(PlatformConfig.id == 1))
    cfg = result.scalar_one_or_none()

    defaults = {
        "essential_monthly_pence": 1199,
        "essential_annual_pence": 11990,
        "premium_monthly_pence": 1899,
        "premium_annual_pence": 18990,
        "elite_monthly_pence": 2399,
        "elite_annual_pence": 23990,
        "blue_tick_setup_pence": 1000,
        "blue_tick_monthly_pence": 399,
    }

    if not cfg:
        return defaults

    return {k: getattr(cfg, k) for k in defaults}
