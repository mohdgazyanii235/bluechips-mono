import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escort_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("escorts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Level: 2=identity/age, 3=blue_tick
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    # Submitted documents (S3 keys or local paths)
    id_document_url: Mapped[Optional[str]] = mapped_column(String(500))
    selfie_url: Mapped[Optional[str]] = mapped_column(String(500))
    match_selfie_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Status: pending, approved, rejected
    status: Mapped[str] = mapped_column(String(20), default="pending")
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100))

    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Stripe refund tracking
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(100))
    stripe_charge_id: Mapped[Optional[str]] = mapped_column(String(100))
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    refund_id: Mapped[Optional[str]] = mapped_column(String(100))

    escort: Mapped["Escort"] = relationship("Escort", back_populates="verifications")
