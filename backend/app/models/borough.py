import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Borough(Base):
    __tablename__ = "boroughs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    seo_title: Mapped[str | None] = mapped_column(String(70))
    seo_description: Mapped[str | None] = mapped_column(String(160))
    is_premium_area: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=99)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    escorts: Mapped[list["Escort"]] = relationship("Escort", back_populates="borough")

    def __repr__(self) -> str:
        return f"<Borough {self.name}>"
