from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class WebhookEvent(Base):
    """Tracks Stripe webhook event IDs to enforce idempotent processing.

    Stripe explicitly allows duplicate webhook delivery. Inserting the event_id
    on receipt (with ON CONFLICT DO NOTHING) ensures each event runs at most
    once, even under simultaneous deliveries.
    """
    __tablename__ = "webhook_events"

    # Stripe event IDs look like "evt_1NXyZ..." — fits comfortably in 100 chars
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
