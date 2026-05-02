import secrets
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.routers import auth, escorts, boroughs, upload, verification, admin, payments


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


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Bluechips London API", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred", "code": "INTERNAL_ERROR"},
    )
