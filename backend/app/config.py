from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Bluechips London"
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://bluechips:bluechips_secret@db:5432/bluechips_london"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Security
    SECRET_KEY: str = "insecure-dev-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_ESSENTIAL_PRICE_ID: str = ""           # £24.99/month
    STRIPE_PREMIUM_PRICE_ID: str = ""             # £49.99/month
    STRIPE_ELITE_PRICE_ID: str = ""               # £89.99/month
    STRIPE_ESSENTIAL_ANNUAL_PRICE_ID: str = ""    # £249.90/year (2 months free)
    STRIPE_PREMIUM_ANNUAL_PRICE_ID: str = ""      # £499.90/year (2 months free)
    STRIPE_ELITE_ANNUAL_PRICE_ID: str = ""        # £899.90/year (2 months free)
    STRIPE_BLUE_TICK_SETUP_PRICE_ID: str = ""     # one-time £10
    STRIPE_BLUE_TICK_MONTHLY_PRICE_ID: str = ""   # recurring £3.99/month

    # Email
    EMAIL_FROM: str = "noreply@bluechips.live"
    EMAIL_FROM_NAME: str = "Bluechips London"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Admin — ADMIN_INITIAL_PASSWORD must be set in .env; leave blank to auto-generate on first boot
    ADMIN_EMAIL: str = "mohdgazyanii235@gmail.com"
    ADMIN_INITIAL_PASSWORD: str = ""

    # AWS S3 — OR Cloudflare R2 (S3-compatible, free 10GB tier)
    # For R2: set S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "auto"
    S3_BUCKET_NAME: str = "bluechips-media"
    S3_ENDPOINT_URL: str = ""          # Only needed for R2/non-AWS. Leave blank for real S3.
    S3_PUBLIC_URL: str = ""            # Public base URL for served files (R2 custom domain or CloudFront)
    CLOUDFRONT_URL: str = ""           # Legacy alias — same as S3_PUBLIC_URL

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 10
    LOCAL_UPLOADS_DIR: str = "/app/uploads"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def use_s3(self) -> bool:
        return bool(self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY)

    @property
    def public_media_url(self) -> str:
        return self.S3_PUBLIC_URL or self.CLOUDFRONT_URL or ""

    @property
    def use_stripe(self) -> bool:
        return bool(self.STRIPE_SECRET_KEY)

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
