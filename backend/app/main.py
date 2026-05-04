import secrets
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.routers import auth, escorts, boroughs, upload, verification, admin, payments, discounts, pricing


_DEFAULT_PRICES = {
    "essential_monthly_pence": 1199,
    "essential_annual_pence": 11990,
    "premium_monthly_pence": 1899,
    "premium_annual_pence": 18990,
    "elite_monthly_pence": 2399,
    "elite_annual_pence": 23990,
    "blue_tick_setup_pence": 1000,
    "blue_tick_monthly_pence": 399,
}

_STRIPE_ID_MAP = {
    "stripe_essential_monthly_id": "STRIPE_ESSENTIAL_PRICE_ID",
    "stripe_essential_annual_id": "STRIPE_ESSENTIAL_ANNUAL_PRICE_ID",
    "stripe_premium_monthly_id": "STRIPE_PREMIUM_PRICE_ID",
    "stripe_premium_annual_id": "STRIPE_PREMIUM_ANNUAL_PRICE_ID",
    "stripe_elite_monthly_id": "STRIPE_ELITE_PRICE_ID",
    "stripe_elite_annual_id": "STRIPE_ELITE_ANNUAL_PRICE_ID",
    "stripe_blue_tick_setup_id": "STRIPE_BLUE_TICK_SETUP_PRICE_ID",
    "stripe_blue_tick_monthly_id": "STRIPE_BLUE_TICK_MONTHLY_PRICE_ID",
}


async def _ensure_platform_config():
    """Seed the singleton platform_config row with defaults and Stripe IDs from config."""
    from sqlalchemy import select
    from app.models.platform_config import PlatformConfig

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(PlatformConfig).where(PlatformConfig.id == 1))
        cfg = result.scalar_one_or_none()
        if not cfg:
            cfg = PlatformConfig(id=1)
            db.add(cfg)

        # Seed default prices if they are 0 or None (handles fresh DB or bad migration)
        for field, default_value in _DEFAULT_PRICES.items():
            if not getattr(cfg, field, None):
                setattr(cfg, field, default_value)

        # Sync Stripe price IDs from .env if the DB field is still blank
        for db_field, config_field in _STRIPE_ID_MAP.items():
            if not getattr(cfg, db_field, None):
                env_value = getattr(settings, config_field, "")
                if env_value:
                    setattr(cfg, db_field, env_value)

        await db.commit()


async def _ensure_admin_exists():
    from sqlalchemy import select
    from app.models.admin import Admin
    from app.utils.security import hash_password

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Admin).where(Admin.email == settings.ADMIN_EMAIL))
        if result.scalar_one_or_none():
            return

        password = settings.ADMIN_INITIAL_PASSWORD or secrets.token_urlsafe(16)
        admin_obj = Admin(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(password),
        )
        db.add(admin_obj)
        await db.commit()
        if not settings.ADMIN_INITIAL_PASSWORD:
            print(f"\n{'='*60}")
            print(f"  Admin account created: {settings.ADMIN_EMAIL}")
            print(f"  Auto-generated password: {password}")
            print(f"  IMPORTANT: Save this password and set ADMIN_INITIAL_PASSWORD in .env")
            print(f"{'='*60}\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate production security settings
    _DEV_SECRET = "insecure-dev-key-change-in-production"
    if settings.APP_ENV == "production" and settings.SECRET_KEY == _DEV_SECRET:
        raise RuntimeError(
            "FATAL: SECRET_KEY is set to the insecure development default. "
            "Set a strong random SECRET_KEY in .env before running in production."
        )

    for subdir in ["photos", "photos/thumbs", "documents"]:
        Path(settings.LOCAL_UPLOADS_DIR).joinpath(subdir).mkdir(parents=True, exist_ok=True)

    await _ensure_admin_exists()
    await _ensure_platform_config()
    yield


_is_prod = settings.APP_ENV == "production"

app = FastAPI(
    title="Bluechips London API",
    description="Premium Companion Directory — Marketing Platform",
    version="1.0.0",
    docs_url=None if _is_prod else "/api/docs",
    redoc_url=None if _is_prod else "/api/redoc",
    openapi_url=None if _is_prod else "/api/openapi.json",
    lifespan=lifespan,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if _is_prod:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve local uploads in development
uploads_path = Path(settings.LOCAL_UPLOADS_DIR)
if uploads_path.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(escorts.router, prefix="/api")
app.include_router(boroughs.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(verification.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(discounts.router, prefix="/api")
app.include_router(pricing.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Bluechips London API", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
    )
