"""
登录认证与会话管理
AuthContext 全局单例，存储当前登录用户
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import User


class AuthContext:
    _instance: Optional["AuthContext"] = None
    _user: Optional["User"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def user(self) -> Optional["User"]:
        return self._user

    @property
    def is_authenticated(self) -> bool:
        return self._user is not None

    @property
    def role(self) -> str:
        return self._user.role if self._user else ""

    def login(self, user: "User"):
        self._user = user

    def logout(self):
        self._user = None

    def is_super_admin(self) -> bool:
        return self.role == "super_admin"

    def is_engineer(self) -> bool:
        return self.role in ("super_admin", "engineer")

    def is_viewer(self) -> bool:
        return self.role in ("super_admin", "engineer", "viewer")
