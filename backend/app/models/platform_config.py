import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class PlatformConfig(Base):
    """Singleton row (id=1) storing admin-configurable pricing and Stripe price IDs."""
    __tablename__ = "platform_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # Display / charge prices in pence (GBP)
    essential_monthly_pence: Mapped[int] = mapped_column(Integer, default=1199)
    essential_annual_pence: Mapped[int] = mapped_column(Integer, default=11990)
    premium_monthly_pence: Mapped[int] = mapped_column(Integer, default=1899)
    premium_annual_pence: Mapped[int] = mapped_column(Integer, default=18990)
    elite_monthly_pence: Mapped[int] = mapped_column(Integer, default=2399)
    elite_annual_pence: Mapped[int] = mapped_column(Integer, default=23990)
    blue_tick_setup_pence: Mapped[int] = mapped_column(Integer, default=1000)
    blue_tick_monthly_pence: Mapped[int] = mapped_column(Integer, default=399)

    # Stripe Price IDs — seeded from config.py on first boot, updated by admin
    stripe_essential_monthly_id: Mapped[str] = mapped_column(String(200), default="")
    stripe_essential_annual_id: Mapped[str] = mapped_column(String(200), default="")
    stripe_premium_monthly_id: Mapped[str] = mapped_column(String(200), default="")
    stripe_premium_annual_id: Mapped[str] = mapped_column(String(200), default="")
    stripe_elite_monthly_id: Mapped[str] = mapped_column(String(200), default="")
    stripe_elite_annual_id: Mapped[str] = mapped_column(String(200), default="")
    stripe_blue_tick_setup_id: Mapped[str] = mapped_column(String(200), default="")
    stripe_blue_tick_monthly_id: Mapped[str] = mapped_column(String(200), default="")

    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
