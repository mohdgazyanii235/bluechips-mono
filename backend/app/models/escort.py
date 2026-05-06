import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database import Base
import enum


class SubscriptionTier(str, enum.Enum):
    free = "free"
    essential = "essential"
    premium = "premium"
    elite = "elite"


class AvailabilityType(str, enum.Enum):
    incall = "incall"
    outcall = "outcall"
    both = "both"


class BuildType(str, enum.Enum):
    slim = "slim"
    athletic = "athletic"
    curvy = "curvy"
    petite = "petite"
    bbw = "bbw"


class VerificationLevel(int, enum.Enum):
    none = 0
    email = 1
    identity = 2
    blue_tick = 3


class Escort(Base):
    __tablename__ = "escorts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Auth
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Identity (anonymised)
    stage_name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)

    # Physical profile
    age: Mapped[Optional[int]] = mapped_column(Integer)
    nationality: Mapped[Optional[str]] = mapped_column(String(80))
    ethnicity: Mapped[Optional[str]] = mapped_column(String(80))
    height_cm: Mapped[Optional[int]] = mapped_column(Integer)
    build: Mapped[Optional[str]] = mapped_column(String(20))
    hair_colour: Mapped[Optional[str]] = mapped_column(String(50))
    eye_colour: Mapped[Optional[str]] = mapped_column(String(50))
    dress_size: Mapped[Optional[str]] = mapped_column(String(20))
    chest: Mapped[Optional[str]] = mapped_column(String(30))

    # Location
    borough_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("boroughs.id"), index=True)
    availability_type: Mapped[Optional[str]] = mapped_column(String(10), default="both")

    # Rates (in GBP)
    rate_30min: Mapped[Optional[int]] = mapped_column(Integer)
    rate_1hour: Mapped[Optional[int]] = mapped_column(Integer)
    rate_2hours: Mapped[Optional[int]] = mapped_column(Integer)
    rate_overnight: Mapped[Optional[int]] = mapped_column(Integer)

    # Content
    about_me: Mapped[Optional[str]] = mapped_column(String(600))
    languages: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)
    booking_notice: Mapped[Optional[str]] = mapped_column(String(100))

    # Health
    std_tested: Mapped[bool] = mapped_column(Boolean, default=False)
    std_tested_date: Mapped[Optional[str]] = mapped_column(String(20))

    # Profile type
    profile_type: Mapped[str] = mapped_column(String(20), default="individual")

    # Verification
    verification_level: Mapped[int] = mapped_column(Integer, default=0)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255))
    email_verification_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    available_now: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    # Contact (revealed only after click)
    whatsapp_number: Mapped[Optional[str]] = mapped_column(String(30))
    phone_number: Mapped[Optional[str]] = mapped_column(String(30))

    # Subscription
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(100))
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Blue Tick (separate paid add-on)
    blue_tick_active: Mapped[bool] = mapped_column(Boolean, default=False)
    blue_tick_stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Referral
    referral_code: Mapped[Optional[str]] = mapped_column(String(10), unique=True, nullable=True, index=True)
    referred_by_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    referral_reward_claimed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Stats
    profile_views: Mapped[int] = mapped_column(Integer, default=0)
    contact_clicks: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    borough: Mapped[Optional["Borough"]] = relationship("Borough", back_populates="escorts")
    photos: Mapped[list["EscortPhoto"]] = relationship("EscortPhoto", back_populates="escort", cascade="all, delete-orphan", order_by="EscortPhoto.sort_order")
    services: Mapped[list["EscortService"]] = relationship("EscortService", back_populates="escort", cascade="all, delete-orphan")
    verifications: Mapped[list["Verification"]] = relationship("Verification", back_populates="escort", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship("Subscription", back_populates="escort", cascade="all, delete-orphan")
    boosts: Mapped[list["Boost"]] = relationship("Boost", back_populates="escort", cascade="all, delete-orphan")

    @property
    def primary_photo_url(self) -> Optional[str]:
        primary = next((p for p in self.photos if p.is_primary), None)
        if primary:
            return primary.url
        return self.photos[0].url if self.photos else None

    @property
    def photo_limit(self) -> int:
        limits = {"free": 3, "essential": 8, "premium": 50, "elite": 50}
        return limits.get(self.subscription_tier, 3)

    def __repr__(self) -> str:
        return f"<Escort {self.stage_name}>"


class EscortPhoto(Base):
    __tablename__ = "escort_photos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escort_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("escorts.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    escort: Mapped["Escort"] = relationship("Escort", back_populates="photos")


class EscortService(Base):
    __tablename__ = "escort_services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escort_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("escorts.id", ondelete="CASCADE"), nullable=False, index=True)
    tag: Mapped[str] = mapped_column(String(50), nullable=False)

    escort: Mapped["Escort"] = relationship("Escort", back_populates="services")
