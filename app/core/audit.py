"""
审计日志写入工具
"""
import json
from typing import Optional, Any
from app.core.auth import AuthContext


def write_audit(
    operation_type: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    data_before: Optional[Any] = None,
    data_after: Optional[Any] = None,
    detail: Optional[str] = None,
    operator_name: Optional[str] = None,
    operator_id: Optional[str] = None,
):
    """
    写入一条审计日志。
    优先从 AuthContext 获取操作人信息；传入参数可覆盖（用于登录失败等无会话场景）。
    """
    from app.models import AuditLog
    from app.utils.db import get_session

    ctx = AuthContext()
    op_id = operator_id or (ctx.user.id if ctx.user else None)
    op_name = operator_name or (ctx.user.display_name if ctx.user else "系统")

    log = AuditLog(
        operator_id=op_id,
        operator_name=op_name,
        operation_type=operation_type,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        data_before=json.dumps(data_before, ensure_ascii=False) if data_before is not None else None,
        data_after=json.dumps(data_after, ensure_ascii=False) if data_after is not None else None,
        detail=detail,
    )
    with get_session() as session:
        session.add(log)
        session.commit()
