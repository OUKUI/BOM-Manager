"""
零件母表模型
"""
from typing import Optional
from sqlalchemy import String, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin, SoftDeleteMixin


class PartsMaster(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "parts_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    version: Mapped[str] = mapped_column(String(16), nullable=False)
    standard_level: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)   # 主要/要/次要
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    spec_material: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    default_qty: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # FK users.id
    updated_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    def __repr__(self) -> str:
        return f"<Part {self.part_number} v{self.version}>"
