import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escort_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("escorts.id", ondelete="CASCADE"), nullable=False, index=True)

    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, cancelled, expired, trialing

    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(100))
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(100))

    amount_gbp: Mapped[Optional[int]] = mapped_column(Integer)  # in pence
    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    # Pending downgrade: the tier to switch to when the current billing period ends.
    # Set when a user downgrades mid-cycle; cleared once the webhook fires on renewal.
    pending_tier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    escort: Mapped["Escort"] = relationship("Escort", back_populates="subscriptions")


class Boost(Base):
    __tablename__ = "boosts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escort_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("escorts.id", ondelete="CASCADE"), nullable=False, index=True)

    boost_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: spotlight_7d, hot_24h, new_to_london, weekend_warrior, extra_borough
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(100))
    amount_gbp: Mapped[Optional[int]] = mapped_column(Integer)  # in pence

    starts_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    escort: Mapped["Escort"] = relationship("Escort", back_populates="boosts")
