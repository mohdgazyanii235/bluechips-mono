import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class DiscountCode(Base):
    __tablename__ = "discount_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    percent_off: Mapped[int] = mapped_column(Integer, nullable=False)
    applicable_tiers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    max_redemptions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_redemptions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
