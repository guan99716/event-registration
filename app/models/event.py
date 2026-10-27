from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, ForeignKey, func

from app.models.base import Base


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(200))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int]
    registered_count: Mapped[int] = mapped_column(server_default="0")
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
