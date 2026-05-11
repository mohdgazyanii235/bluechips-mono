import random
import string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from app.database import get_db
from app.models.escort import Escort
from app.models.discount import DiscountCode
from app.models.outreach import OutreachProspect
from app.models.platform_config import PlatformConfig
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, PasswordChangeRequest
from app.schemas.common import MessageResponse
from app.utils.security import hash_password, verify_password, create_access_token, generate_verification_token
from app.utils.slugify import make_slug, make_unique_slug
from app.utils.rate_limit import is_rate_limited
from app.services.email_service import send_verification_email, send_welcome_email
from app.routers.deps import get_current_escort


async def _unique_referral_code(db: AsyncSession) -> str:
    for _ in range(20):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        exists = await db.execute(select(Escort.id).where(Escort.referral_code == code))
        if not exists.scalar_one_or_none():
            return code
    raise RuntimeError("Could not generate a unique referral code")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"register:{client_ip}", max_attempts=5, window_seconds=3600):
        raise HTTPException(status_code=429, detail="Too many registration attempts. Please try again later.")

    existing = await db.execute(select(Escort).where(Escort.email == data.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    all_slugs_result = await db.execute(select(Escort.slug))
    existing_slugs = {row[0] for row in all_slugs_result.fetchall()}
    slug = make_unique_slug(data.stage_name, existing_slugs)

    token = generate_verification_token()
    token_expiry = datetime.utcnow() + timedelta(hours=24)
    referral_code = await _unique_referral_code(db)

    # Optional: pre-validate invite/discount code so we can attach it at signup
    discount_code_id = None
    is_founding = False
    if data.invite_code:
        code_str = data.invite_code.strip().upper()
        dc_result = await db.execute(
            select(DiscountCode).where(DiscountCode.code == code_str, DiscountCode.is_active == True)
        )
        dc = dc_result.scalar_one_or_none()
        if dc and (dc.max_redemptions is None or dc.current_redemptions < dc.max_redemptions):
            discount_code_id = dc.id
            # If this is a founding-member code (single-use, name prefix matches), mark founding
            cfg_result = await db.execute(select(PlatformConfig).where(PlatformConfig.id == 1))
            cfg = cfg_result.scalar_one_or_none()
            if cfg and cfg.founding_offer_active and code_str.startswith("FM-"):
                # Check if there's room left
                if cfg.founding_offer_signups < cfg.founding_offer_limit:
                    is_founding = True

    escort = Escort(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        stage_name=data.stage_name.strip(),
        slug=slug,
        email_verification_token=token,
        email_verification_token_expires_at=token_expiry,
        verification_level=0,
        referral_code=referral_code,
        signup_discount_code_id=discount_code_id,
        is_founding_member=is_founding,
        founding_member_since=datetime.utcnow() if is_founding else None,
    )
    db.add(escort)
    await db.flush()

    # Link the prospect (if any) and increment founding counter
    if discount_code_id:
        prospect_result = await db.execute(
            select(OutreachProspect).where(OutreachProspect.discount_code_id == discount_code_id)
        )
        prospect = prospect_result.scalar_one_or_none()
        if prospect and not prospect.converted_escort_id:
            prospect.converted_escort_id = escort.id
            prospect.signed_up_at = datetime.utcnow()
            prospect.status = "signed_up"

        if is_founding:
            cfg_result = await db.execute(select(PlatformConfig).where(PlatformConfig.id == 1))
            cfg = cfg_result.scalar_one_or_none()
            if cfg:
                cfg.founding_offer_signups += 1

    background_tasks.add_task(send_verification_email, escort.email, escort.stage_name, token)
    return MessageResponse(message="Account created! Please check your email to verify your account.")


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"login:{client_ip}:{data.email.lower()}"
    if is_rate_limited(rate_key, max_attempts=10, window_seconds=600):
        raise HTTPException(status_code=429, detail="Too many login attempts. Please wait 10 minutes.")

    result = await db.execute(select(Escort).where(Escort.email == data.email.lower()))
    escort = result.scalar_one_or_none()
    if not escort or not verify_password(data.password, escort.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not escort.is_active:
        raise HTTPException(status_code=403, detail="Your account has been deactivated")

    token = create_access_token(str(escort.id))
    return TokenResponse(
        access_token=token,
        escort_id=str(escort.id),
        stage_name=escort.stage_name,
        subscription_tier=escort.subscription_tier,
        verification_level=escort.verification_level,
        profile_complete=escort.profile_complete,
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    token: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Escort).where(Escort.email_verification_token == token))
    escort = result.scalar_one_or_none()
    if not escort:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")
    if escort.is_email_verified:
        return MessageResponse(message="Email already verified")

    if (
        escort.email_verification_token_expires_at is not None
        and escort.email_verification_token_expires_at < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=400,
            detail="This verification link has expired (links are valid for 24 hours). Please register again."
        )

    escort.is_email_verified = True
    escort.verification_level = max(escort.verification_level, 1)
    escort.email_verification_token = None
    await db.flush()

    background_tasks.add_task(send_welcome_email, escort.email, escort.stage_name)
    return MessageResponse(message="Email verified successfully! Welcome to Bluechips London.")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: PasswordChangeRequest,
    escort: Escort = Depends(get_current_escort),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.current_password, escort.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    escort.hashed_password = hash_password(data.new_password)
    return MessageResponse(message="Password updated successfully")
