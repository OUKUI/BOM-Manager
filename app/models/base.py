"""
ORM 基础类：DeclarativeBase + SoftDeleteMixin + TimestampMixin
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class SoftDeleteMixin:
    is_deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def soft_delete(self):
        self.is_deleted = 1
