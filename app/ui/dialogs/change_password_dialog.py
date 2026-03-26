"""
强制改密对话框（首次登录 / 超管重置后）
"""
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, PasswordLineEdit,
    InfoBar, InfoBarPosition
)
from app.utils.security import hash_password, check_password_strength
from app.utils.db import get_session
from app.models import User


class ChangePasswordDialog(MessageBoxBase):
    def __init__(self, user: User, force: bool = False, parent=None):
        super().__init__(parent)
        self._user = user

        self.titleLabel = SubtitleLabel(
            "首次登录请修改密码" if force else "修改密码", self
        )

        self.new_pwd = PasswordLineEdit(self)
        self.new_pwd.setPlaceholderText("新密码")

        self.confirm_pwd = PasswordLineEdit(self)
        self.confirm_pwd.setPlaceholderText("确认新密码")

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(self.new_pwd)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addWidget(self.confirm_pwd)

        self.yesButton.setText("确认修改")
        self.cancelButton.setText("取消")
        if force:
            self.cancelButton.hide()

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

        with get_session() as session:
            u = session.get(User, self._user.id)
            u.password_hash = hash_password(new)
            u.must_change_pwd = 0
            session.commit()

        from app.core.audit import write_audit
        write_audit("RESET_PASSWORD", resource_type="USER",
                    resource_id=self._user.id,
                    detail=f"用户 {self._user.username} 修改了自己的密码")
        return True
