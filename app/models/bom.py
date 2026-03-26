"""
BOM 项目表 + BOM 明细表
"""
from typing import Optional
from sqlalchemy import String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin, SoftDeleteMixin, _new_uuid


class BomProject(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "bom_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    bom_number: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_part_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    customer_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    current_version: Mapped[str] = mapped_column(String(16), nullable=False, default="A01")
    established_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)   # YYYY-MM-DD
    updated_date: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")    # active / archived
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    def __repr__(self) -> str:
        return f"<BomProject {self.bom_number} v{self.current_version}>"


class BomItem(Base, SoftDeleteMixin):
    __tablename__ = "bom_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bom_project_id: Mapped[str] = mapped_column(String(36), ForeignKey("bom_projects.id"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    level_mark: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)    # *, ■, 空
    level_label: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)   # 一/二/三
    part_number: Mapped[str] = mapped_column(String(64), nullable=False)
    part_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # JSON
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    updated_at: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    def __repr__(self) -> str:
        return f"<BomItem L{self.level} {self.part_number} x{self.quantity}>"
