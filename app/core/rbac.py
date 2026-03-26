"""
RBAC 权限装饰器
用法：在 service 层函数上加 @require_role("super_admin") 或 @require_role("engineer", "super_admin")
"""
import functools
from app.core.auth import AuthContext


class PermissionDenied(Exception):
    pass


def require_role(*allowed_roles: str):
    """
    装饰器：调用被装饰函数前检查当前用户角色。
    若角色不在 allowed_roles 中，抛出 PermissionDenied。
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ctx = AuthContext()
            if not ctx.is_authenticated:
                raise PermissionDenied("未登录，无法执行该操作")
            if ctx.role not in allowed_roles:
                raise PermissionDenied(
                    f"权限不足：当前角色 [{ctx.role}]，需要 {list(allowed_roles)}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
