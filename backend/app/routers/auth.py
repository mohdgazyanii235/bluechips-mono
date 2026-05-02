from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.escort import Escort
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, PasswordChangeRequest
from app.schemas.common import MessageResponse
from app.utils.security import hash_password, verify_password, create_access_token, generate_verification_token
from app.utils.slugify import make_slug, make_unique_slug
from app.utils.rate_limit import is_rate_limited
from app.services.email_service import send_verification_email, send_welcome_email
from app.routers.deps import get_current_escort

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
    escort = Escort(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        stage_name=data.stage_name.strip(),
        slug=slug,
        email_verification_token=token,
        email_verification_token_expires_at=token_expiry,
        verification_level=0,
    )
    db.add(escort)
    await db.flush()

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
