"""
变更履历表 + 系统审计日志
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin, _utcnow


class BomChangeLog(Base):
    __tablename__ = "bom_change_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bom_project_id: Mapped[str] = mapped_column(String(36), ForeignKey("bom_projects.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    change_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    previous_version: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    new_version: Mapped[str] = mapped_column(String(16), nullable=False)
    changed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)   # FK users.id
    changed_by_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # 快照
    change_date: Mapped[str] = mapped_column(String(16), nullable=False)            # YYYY-MM-DD
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bom_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)        # JSON 完整明细快照

    def __repr__(self) -> str:
        return f"<BomChangeLog seq={self.sequence} {self.previous_version}->{self.new_version}>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operator_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    operator_name: Mapped[str] = mapped_column(String(64), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # LOGIN_SUCCESS / LOGIN_FAIL / LOGOUT / CREATE / UPDATE / SOFT_DELETE /
    # RESTORE / EXPORT / IMPORT / RESET_PASSWORD / CHANGE_ROLE
    resource_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    data_before: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # JSON
    data_after: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # JSON
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.operation_type} by {self.operator_name}>"
