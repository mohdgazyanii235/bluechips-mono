from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.borough import Borough
from app.models.escort import Escort
from app.schemas.borough import BoroughOut

router = APIRouter(prefix="/boroughs", tags=["Boroughs"])


@router.get("", response_model=list[BoroughOut])
async def list_boroughs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Borough,
            func.count(Escort.id).label("escort_count"),
        )
        .outerjoin(Escort, (Escort.borough_id == Borough.id) & (Escort.is_active == True) & (Escort.is_approved == True))
        .group_by(Borough.id)
        .order_by(Borough.sort_order, Borough.name)
    )
    rows = result.all()
    return [
        BoroughOut(
            id=b.id, name=b.name, slug=b.slug, description=b.description,
            seo_title=b.seo_title, seo_description=b.seo_description,
            is_premium_area=b.is_premium_area, escort_count=count,
        )
        for b, count in rows
    ]


@router.get("/{slug}", response_model=BoroughOut)
async def get_borough(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Borough, func.count(Escort.id).label("escort_count"))
        .outerjoin(Escort, (Escort.borough_id == Borough.id) & (Escort.is_active == True))
        .where(Borough.slug == slug)
        .group_by(Borough.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Borough not found")
    b, count = row
    return BoroughOut(
        id=b.id, name=b.name, slug=b.slug, description=b.description,
        seo_title=b.seo_title, seo_description=b.seo_description,
        is_premium_area=b.is_premium_area, escort_count=count,
    )
