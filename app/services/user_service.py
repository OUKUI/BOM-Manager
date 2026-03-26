"""
用户服务：增删改查 + 密码重置
"""
from typing import Optional
from datetime import datetime, timezone
from app.models import User
from app.utils.db import get_session
from app.utils.security import hash_password, check_password_strength
from app.core.rbac import require_role
from app.core.audit import write_audit


def get_all_users(include_deleted: bool = False) -> list[User]:
    with get_session() as s:
        q = s.query(User)
        if not include_deleted:
            q = q.filter_by(is_deleted=0)
        return q.order_by(User.created_at).all()


def get_user_by_id(user_id: str) -> Optional[User]:
    with get_session() as s:
        return s.query(User).filter_by(id=user_id, is_deleted=0).first()


def get_user_by_username(username: str) -> Optional[User]:
    with get_session() as s:
        return s.query(User).filter_by(username=username, is_deleted=0).first()


@require_role("super_admin")
def create_user(username: str, display_name: str, role: str, initial_password: str) -> User:
    ok, msg = check_password_strength(initial_password)
    if not ok:
        raise ValueError(msg)
    if role not in ("super_admin", "engineer", "viewer"):
        raise ValueError(f"无效角色: {role}")

    existing = get_user_by_username(username)
    if existing:
        raise ValueError(f"用户名 '{username}' 已存在")

    user = User(
        username=username,
        password_hash=hash_password(initial_password),
        role=role,
        display_name=display_name,
        must_change_pwd=1,
    )
    with get_session() as s:
        s.add(user)
        s.commit()
        s.refresh(user)

    write_audit("CREATE", resource_type="USER", resource_id=user.id,
                data_after={"username": username, "role": role})
    return user


@require_role("super_admin")
def update_user(user_id: str, display_name: str = None, role: str = None) -> User:
    with get_session() as s:
        user = s.get(User, user_id)
        if not user or user.is_deleted:
            raise ValueError("用户不存在")

        before = {"display_name": user.display_name, "role": user.role}
        if display_name is not None:
            user.display_name = display_name
        if role is not None:
            if role not in ("super_admin", "engineer", "viewer"):
                raise ValueError(f"无效角色: {role}")
            user.role = role
        s.commit()
        s.refresh(user)

    write_audit("UPDATE", resource_type="USER", resource_id=user_id,
                data_before=before,
                data_after={"display_name": user.display_name, "role": user.role})
    return user


@require_role("super_admin")
def reset_user_password(user_id: str, new_password: str):
    ok, msg = check_password_strength(new_password)
    if not ok:
        raise ValueError(msg)

    with get_session() as s:
        user = s.get(User, user_id)
        if not user or user.is_deleted:
            raise ValueError("用户不存在")
        user.password_hash = hash_password(new_password)
        user.must_change_pwd = 1
        s.commit()

    write_audit("RESET_PASSWORD", resource_type="USER", resource_id=user_id,
                detail=f"超管重置了用户 {user_id} 的密码")


@require_role("super_admin")
def soft_delete_user(user_id: str):
    from app.core.auth import AuthContext
    if AuthContext().user and AuthContext().user.id == user_id:
        raise ValueError("不能删除当前登录账户")

    with get_session() as s:
        user = s.get(User, user_id)
        if not user or user.is_deleted:
            raise ValueError("用户不存在")
        before = {"username": user.username, "role": user.role}
        user.soft_delete()
        s.commit()

    write_audit("SOFT_DELETE", resource_type="USER", resource_id=user_id,
                data_before=before)
