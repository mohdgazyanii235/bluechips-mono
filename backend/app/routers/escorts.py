from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
from typing import Optional
from app.database import get_db
from app.models.escort import Escort, EscortPhoto, EscortService
from app.models.borough import Borough
from app.schemas.escort import (
    EscortCardOut, EscortProfileOut, EscortUpdateRequest,
    EscortDashboardOut, EscortSearchParams,
)
from app.schemas.common import PaginatedResponse, MessageResponse
from app.routers.deps import get_current_escort, get_current_verified_escort
from app.utils.slugify import make_slug, make_unique_slug

router = APIRouter(prefix="/escorts", tags=["Escorts"])

ALLOWED_SERVICE_TAGS = {
    "GFE", "PSE", "OWO", "OWO-CIM", "Massage", "Erotic Massage", "Tantric Massage",
    "Happy Ending", "DFK", "69", "Anal", "COB", "Deep Throat", "FF", "Rimming",
    "BDSM", "Bondage", "Domination", "Submission", "Fetish", "Role Play", "Duo",
    "Couples Welcome", "Dinner Date", "Travel Companion", "Overnight", "Watersports",
    "Toys", "Striptease", "Lap Dance", "Foot Fetish", "Strapon", "CBT",
}


def _build_card(escort: Escort) -> EscortCardOut:
    return EscortCardOut(
        id=escort.id,
        stage_name=escort.stage_name,
        slug=escort.slug,
        age=escort.age,
        nationality=escort.nationality,
        ethnicity=escort.ethnicity,
        borough_name=escort.borough.name if escort.borough else None,
        borough_slug=escort.borough.slug if escort.borough else None,
        availability_type=escort.availability_type,
        rate_1hour=escort.rate_1hour,
        subscription_tier=escort.subscription_tier,
        verification_level=escort.verification_level,
        available_now=escort.available_now,
        std_tested=escort.std_tested,
        primary_photo_url=escort.primary_photo_url,
        service_tags=[s.tag for s in escort.services[:4]],
        profile_type=escort.profile_type,
    )


def _build_profile(escort: Escort) -> EscortProfileOut:
    return EscortProfileOut(
        id=escort.id,
        stage_name=escort.stage_name,
        slug=escort.slug,
        age=escort.age,
        nationality=escort.nationality,
        ethnicity=escort.ethnicity,
        height_cm=escort.height_cm,
        build=escort.build,
        hair_colour=escort.hair_colour,
        eye_colour=escort.eye_colour,
        dress_size=escort.dress_size,
        chest=escort.chest,
        borough_name=escort.borough.name if escort.borough else None,
        borough_slug=escort.borough.slug if escort.borough else None,
        availability_type=escort.availability_type,
        rate_30min=escort.rate_30min,
        rate_1hour=escort.rate_1hour,
        rate_2hours=escort.rate_2hours,
        rate_overnight=escort.rate_overnight,
        about_me=escort.about_me,
        languages=escort.languages,
        booking_notice=escort.booking_notice,
        std_tested=escort.std_tested,
        std_tested_date=escort.std_tested_date,
        subscription_tier=escort.subscription_tier,
        verification_level=escort.verification_level,
        blue_tick_active=escort.blue_tick_active,
        available_now=escort.available_now,
        profile_views=escort.profile_views,
        service_tags=[s.tag for s in escort.services],
        photos=[{"id": p.id, "url": p.url, "thumbnail_url": p.thumbnail_url,
                 "is_primary": p.is_primary, "sort_order": p.sort_order}
                for p in escort.photos],
        created_at=escort.created_at,
        profile_type=escort.profile_type,
        whatsapp_number=escort.whatsapp_number,
        phone_number=escort.phone_number,
    )


@router.get("", response_model=PaginatedResponse[EscortCardOut])
async def list_escorts(
    borough_slug: Optional[str] = Query(None),
    ethnicity: Optional[str] = Query(None),
    availability_type: Optional[str] = Query(None),
    profile_type: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None),
    max_age: Optional[int] = Query(None),
    min_rate: Optional[int] = Query(None),
    max_rate: Optional[int] = Query(None),
    std_tested: Optional[bool] = Query(None),
    available_now: Optional[bool] = Query(None),
    blue_tick_only: Optional[bool] = Query(None),
    service_tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=48),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Escort.is_active == True, Escort.is_approved == True, Escort.is_email_verified == True]

    if borough_slug:
        borough_result = await db.execute(select(Borough).where(Borough.slug == borough_slug))
        borough = borough_result.scalar_one_or_none()
        if borough:
            conditions.append(Escort.borough_id == borough.id)

    if ethnicity:
        conditions.append(Escort.ethnicity == ethnicity)
    if profile_type and profile_type in ("individual", "couple"):
        conditions.append(Escort.profile_type == profile_type)
    if availability_type:
        conditions.append(Escort.availability_type == availability_type)
    if min_age:
        conditions.append(Escort.age >= min_age)
    if max_age:
        conditions.append(Escort.age <= max_age)
    if min_rate:
        conditions.append(Escort.rate_1hour >= min_rate)
    if max_rate:
        conditions.append(Escort.rate_1hour <= max_rate)
    if std_tested is not None:
        conditions.append(Escort.std_tested == std_tested)
    if available_now:
        conditions.append(Escort.available_now == True)
    if blue_tick_only:
        conditions.append(Escort.verification_level >= 3)
    if service_tag:
        conditions.append(
            Escort.id.in_(
                select(EscortService.escort_id).where(EscortService.tag == service_tag)
            )
        )

    count_result = await db.execute(select(func.count()).select_from(Escort).where(and_(*conditions)))
    total = count_result.scalar()

    # Boost priority ordering: elite > premium > essential > free, then verification_level desc, then available_now desc
    tier_order = case(
        (Escort.subscription_tier == "elite", 4),
        (Escort.subscription_tier == "premium", 3),
        (Escort.subscription_tier == "essential", 2),
        (Escort.subscription_tier == "free", 1),
        else_=0,
    )

    result = await db.execute(
        select(Escort)
        .options(selectinload(Escort.borough), selectinload(Escort.photos), selectinload(Escort.services))
        .where(and_(*conditions))
        .order_by(
            tier_order.desc(),
            Escort.verification_level.desc(),
            Escort.available_now.desc(),
            Escort.updated_at.desc(),
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    escorts = result.scalars().all()

    return PaginatedResponse(
        items=[_build_card(e) for e in escorts],
        total=total,
        page=page,
        per_page=per_page,
        pages=-(-total // per_page),
    )


@router.get("/me", response_model=EscortDashboardOut)
async def get_my_profile(escort: Escort = Depends(get_current_escort), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Escort)
        .options(selectinload(Escort.borough), selectinload(Escort.photos), selectinload(Escort.services))
        .where(Escort.id == escort.id)
    )
    full = result.scalar_one()
    # Build from model fields automatically — any new column added to both Escort and
    # EscortDashboardOut is included without touching this endpoint.
    # Relationship-derived fields (borough_name, service_tags, photos) are overridden below.
    data = {
        field: getattr(full, field, None)
        for field in EscortDashboardOut.model_fields
        if hasattr(full, field)
    }
    data["borough_name"] = full.borough.name if full.borough else None
    data["service_tags"] = [s.tag for s in full.services]
    data["photos"] = [
        {"id": p.id, "url": p.url, "thumbnail_url": p.thumbnail_url,
         "is_primary": p.is_primary, "sort_order": p.sort_order}
        for p in full.photos
    ]
    return EscortDashboardOut.model_validate(data)


@router.put("/me", response_model=MessageResponse)
async def update_my_profile(
    data: EscortUpdateRequest,
    escort: Escort = Depends(get_current_escort),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Escort)
        .options(selectinload(Escort.services))
        .where(Escort.id == escort.id)
    )
    db_escort = result.scalar_one()

    update_data = data.model_dump(exclude_unset=True)
    service_tags = update_data.pop("service_tags", None)

    for field, value in update_data.items():
        setattr(db_escort, field, value)

    if service_tags is not None:
        valid_tags = [t for t in service_tags if t in ALLOWED_SERVICE_TAGS]
        for svc in list(db_escort.services):
            await db.delete(svc)
        for tag in valid_tags:
            db.add(EscortService(escort_id=db_escort.id, tag=tag))

    # Compute profile completeness
    required = [db_escort.age, db_escort.borough_id, db_escort.about_me, db_escort.availability_type]
    db_escort.profile_complete = all(f is not None for f in required)

    await db.flush()
    return MessageResponse(message="Profile updated successfully")


@router.patch("/me/available-now", response_model=MessageResponse)
async def toggle_available_now(
    available: bool,
    escort: Escort = Depends(get_current_escort),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Escort).where(Escort.id == escort.id))
    db_escort = result.scalar_one()
    db_escort.available_now = available
    return MessageResponse(message=f"Status updated: {'Available Now' if available else 'Offline'}")


@router.get("/{slug}", response_model=EscortProfileOut)
async def get_escort_profile(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Escort)
        .options(selectinload(Escort.borough), selectinload(Escort.photos), selectinload(Escort.services))
        .where(Escort.slug == slug, Escort.is_active == True, Escort.is_approved == True)
    )
    escort = result.scalar_one_or_none()
    if not escort:
        raise HTTPException(status_code=404, detail="Profile not found")

    escort.profile_views += 1
    await db.flush()

    return _build_profile(escort)


@router.post("/{slug}/contact-click", response_model=MessageResponse)
async def record_contact_click(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Escort).where(Escort.slug == slug))
    escort = result.scalar_one_or_none()
    if escort:
        escort.contact_clicks += 1
        await db.flush()
    return MessageResponse(message="ok")
