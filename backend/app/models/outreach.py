import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


# Status values for the prospect funnel
STATUS_NOT_CONTACTED = "not_contacted"
STATUS_CONTACTED = "contacted"
STATUS_REPLIED = "replied"
STATUS_SIGNED_UP = "signed_up"
STATUS_DECLINED = "declined"

ALLOWED_STATUSES = {
    STATUS_NOT_CONTACTED,
    STATUS_CONTACTED,
    STATUS_REPLIED,
    STATUS_SIGNED_UP,
    STATUS_DECLINED,
}


class OutreachProspect(Base):
    __tablename__ = "outreach_prospects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    x_handle: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    stage_name: Mapped[str] = mapped_column(String(100), nullable=False)
    area: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    specialty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_NOT_CONTACTED, index=True)

    generated_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    discount_code_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discount_codes.id", ondelete="SET NULL"),
        nullable=True,
    )
    converted_escort_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("escorts.id", ondelete="SET NULL"),
        nullable=True,
    )

    contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    signed_up_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    discount_code = relationship("DiscountCode", foreign_keys=[discount_code_id])
