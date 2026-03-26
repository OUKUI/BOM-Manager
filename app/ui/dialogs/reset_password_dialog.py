"""
超管重置任意用户密码对话框
"""
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, PasswordLineEdit,
    InfoBar, InfoBarPosition,
)
from app.utils.security import hash_password, check_password_strength
from app.utils.db import get_session
from app.models import User


class ResetPasswordDialog(MessageBoxBase):
    def __init__(self, user: User, parent=None):
        super().__init__(parent)
        self._user = user

        self.titleLabel = SubtitleLabel(f"重置密码 — {user.display_name}", self)

        self.new_pwd = PasswordLineEdit(self)
        self.new_pwd.setPlaceholderText("新密码")

        self.confirm_pwd = PasswordLineEdit(self)
        self.confirm_pwd.setPlaceholderText("确认新密码")

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(self.new_pwd)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(self.confirm_pwd)

        self.yesButton.setText("确认重置")
        self.cancelButton.setText("取消")

    def validate(self) -> bool:
        new = self.new_pwd.text()
        confirm = self.confirm_pwd.text()

        if new != confirm:
            InfoBar.error("错误", "两次输入的密码不一致",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2500)
            return False

        ok, msg = check_password_strength(new)
        if not ok:
            InfoBar.error("密码强度不足", msg,
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2500)
            return False

        with get_session() as s:
            u = s.get(User, self._user.id)
            u.password_hash = hash_password(new)
            u.must_change_pwd = 1
            s.commit()

        from app.core.audit import write_audit
        write_audit(
            "RESET_PASSWORD", resource_type="USER",
            resource_id=self._user.id,
            detail=f"超管重置了用户 {self._user.username} 的密码",
        )
        return True
