"""
BOM 服务：项目管理 + 明细编辑 + 变更履历 + 历史快照
"""
import json
from typing import Optional
from datetime import datetime, date
from app.models import BomProject, BomItem, BomChangeLog
from app.utils.db import get_session
from app.core.rbac import require_role
from app.core.audit import write_audit
from app.core.auth import AuthContext
from app.services.part_service import get_part_snapshot


# ── 项目 CRUD ──────────────────────────────────────────────────────────────

def get_all_projects(include_deleted: bool = False) -> list[BomProject]:
    with get_session() as s:
        q = s.query(BomProject)
        if not include_deleted:
            q = q.filter_by(is_deleted=0)
        return q.order_by(BomProject.updated_at.desc()).all()


def get_project(project_id: str) -> Optional[BomProject]:
    with get_session() as s:
        return s.query(BomProject).filter_by(id=project_id, is_deleted=0).first()


def search_projects(keyword: str = "") -> list[BomProject]:
    with get_session() as s:
        q = s.query(BomProject).filter_by(is_deleted=0)
        if keyword:
            kw = f"%{keyword}%"
            from sqlalchemy import or_
            q = q.filter(or_(
                BomProject.bom_number.ilike(kw),
                BomProject.customer_part_number.ilike(kw),
                BomProject.project_name.ilike(kw),
            ))
        return q.order_by(BomProject.updated_at.desc()).all()


@require_role("super_admin", "engineer")
def create_project(
    bom_number: str,
    customer_part_number: str = "",
    customer_description: str = "",
    project_name: str = "",
    initial_version: str = "A01",
) -> BomProject:
    today = date.today().isoformat()
    user_id = AuthContext().user.id if AuthContext().user else None

    proj = BomProject(
        bom_number=bom_number,
        customer_part_number=customer_part_number,
        customer_description=customer_description,
        project_name=project_name,
        current_version=initial_version,
        established_date=today,
        updated_date=today,
        created_by=user_id,
        updated_by=user_id,
    )
    with get_session() as s:
        s.add(proj)
        s.commit()
        s.refresh(proj)

    # 写入第一条变更履历（BOM初建）
    _append_change_log(
        bom_project_id=proj.id,
        change_reason="BOM 初建",
        previous_version=None,
        new_version=initial_version,
        items=[],
        change_description="新建 BOM 项目",
    )
    write_audit("CREATE", resource_type="BOM", resource_id=proj.id,
                data_after={"bom_number": bom_number, "version": initial_version})
    return proj


@require_role("super_admin")
def soft_delete_project(project_id: str):
    with get_session() as s:
        proj = s.get(BomProject, project_id)
        if not proj or proj.is_deleted:
            raise ValueError("项目不存在")
        before = {"bom_number": proj.bom_number, "version": proj.current_version}
        proj.soft_delete()
        s.commit()
    write_audit("SOFT_DELETE", resource_type="BOM", resource_id=project_id,
                data_before=before)


@require_role("super_admin")
def archive_project(project_id: str):
    with get_session() as s:
        proj = s.get(BomProject, project_id)
        if not proj or proj.is_deleted:
            raise ValueError("项目不存在")
        proj.status = "archived"
        s.commit()
    write_audit("UPDATE", resource_type="BOM", resource_id=project_id,
                data_after={"status": "archived"})


# ── BOM 明细 CRUD ─────────────────────────────────────────────────────────

def get_items(project_id: str) -> list[BomItem]:
    with get_session() as s:
        return (
            s.query(BomItem)
            .filter_by(bom_project_id=project_id, is_deleted=0)
            .order_by(BomItem.sort_order)
            .all()
        )


@require_role("super_admin", "engineer")
def save_bom(
    project_id: str,
    items_data: list[dict],
    new_version: str,
    change_reason: str,
    change_description: str = "",
    notes: str = "",
):
    """
    保存 BOM：
      1. 对每个 item 写入 part_snapshot
      2. 软删除旧明细，插入新明细
      3. 写入变更履历（含 bom_snapshot）
      4. 更新项目版本号与更新日期
      5. 写入审计日志
    items_data 格式:
      [{"sort_order": int, "level": int, "level_mark": str,
        "level_label": str, "part_number": str, "quantity": float, "notes": str}, ...]
    """
    user_id = AuthContext().user.id if AuthContext().user else None
    today = date.today().isoformat()

    with get_session() as s:
        proj = s.get(BomProject, project_id)
        if not proj or proj.is_deleted:
            raise ValueError("项目不存在")
        prev_version = proj.current_version

        # 软删除旧明细
        old_items = s.query(BomItem).filter_by(
            bom_project_id=project_id, is_deleted=0
        ).all()
        for item in old_items:
            item.soft_delete()

        # 插入新明细（含 part_snapshot）
        new_items = []
        for d in items_data:
            snapshot = get_part_snapshot(d["part_number"])
            item = BomItem(
                bom_project_id=project_id,
                sort_order=d.get("sort_order", 0),
                level=d.get("level", 1),
                level_mark=d.get("level_mark", ""),
                level_label=d.get("level_label", ""),
                part_number=d["part_number"],
                part_snapshot=json.dumps(snapshot, ensure_ascii=False),
                quantity=d.get("quantity", 1.0),
                notes=d.get("notes", ""),
                created_by=user_id,
                created_at=today,
                updated_at=today,
            )
            s.add(item)
            new_items.append(item)

        # 更新项目
        proj.current_version = new_version
        proj.updated_date = today
        proj.updated_by = user_id
        s.commit()

    _append_change_log(
        bom_project_id=project_id,
        change_reason=change_reason,
        previous_version=prev_version,
        new_version=new_version,
        items=items_data,
        change_description=change_description,
        notes=notes,
    )
    write_audit("UPDATE", resource_type="BOM", resource_id=project_id,
                data_before={"version": prev_version},
                data_after={"version": new_version, "reason": change_reason})


# ── 变更履历 ───────────────────────────────────────────────────────────────

def _append_change_log(
    bom_project_id: str,
    change_reason: str,
    previous_version: Optional[str],
    new_version: str,
    items: list,
    change_description: str = "",
    notes: str = "",
):
    user = AuthContext().user
    today = date.today().isoformat()

    with get_session() as s:
        count = s.query(BomChangeLog).filter_by(
            bom_project_id=bom_project_id
        ).count()
        log = BomChangeLog(
            bom_project_id=bom_project_id,
            sequence=count + 1,
            change_description=change_description,
            change_reason=change_reason,
            previous_version=previous_version,
            new_version=new_version,
            changed_by=user.id if user else None,
            changed_by_name=user.display_name if user else "系统",
            change_date=today,
            notes=notes,
            bom_snapshot=json.dumps(items, ensure_ascii=False),
        )
        s.add(log)
        s.commit()


def get_change_logs(project_id: str) -> list[BomChangeLog]:
    with get_session() as s:
        return (
            s.query(BomChangeLog)
            .filter_by(bom_project_id=project_id)
            .order_by(BomChangeLog.sequence.desc())
            .all()
        )


def restore_snapshot(log: BomChangeLog) -> list[dict]:
    """从变更日志快照还原 BOM 明细列表"""
    if not log.bom_snapshot:
        return []
    return json.loads(log.bom_snapshot)
