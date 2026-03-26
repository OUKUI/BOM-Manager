"""
新增/编辑用户对话框
"""
from PySide6.QtWidgets import QFormLayout
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, LineEdit, PasswordLineEdit,
    ComboBox, InfoBar, InfoBarPosition,
)
from app.models import User


class AddUserDialog(MessageBoxBase):
    def __init__(self, user: User = None, parent=None):
        super().__init__(parent)
        self._user = user
        is_edit = user is not None

        self.titleLabel = SubtitleLabel("编辑用户" if is_edit else "新增用户", self)

        form = QFormLayout()
        form.setSpacing(10)

        self.f_username = LineEdit(self)
        self.f_username.setPlaceholderText("4~32位字母/数字/下划线")
        if is_edit:
            self.f_username.setText(user.username)
            self.f_username.setReadOnly(True)

        self.f_display = LineEdit(self)
        self.f_display.setPlaceholderText("显示名称")

        self.f_role = ComboBox(self)
        self.f_role.addItems(["viewer — 查看者", "engineer — 工程师", "super_admin — 超级管理员"])

        self.f_password = PasswordLineEdit(self)
        self.f_password.setPlaceholderText("初始密码（首次登录须修改）")

        form.addRow("用户名 *", self.f_username)
        form.addRow("显示名称 *", self.f_display)
        form.addRow("角色 *", self.f_role)
        if not is_edit:
            form.addRow("初始密码 *", self.f_password)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addLayout(form)

        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

        if is_edit:
            self.f_display.setText(user.display_name or "")
            role_map = {"viewer": 0, "engineer": 1, "super_admin": 2}
            self.f_role.setCurrentIndex(role_map.get(user.role, 0))

    def validate(self) -> bool:
        if not self.f_username.text().strip():
            InfoBar.error("错误", "用户名不能为空",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2000)
            return False
        if not self.f_display.text().strip():
            InfoBar.error("错误", "显示名称不能为空",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2000)
            return False
        if self._user is None and not self.f_password.text():
            InfoBar.error("错误", "初始密码不能为空",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2000)
            return False
        return True

    def get_data(self) -> dict:
        role_vals = ["viewer", "engineer", "super_admin"]
        data = {
            "username": self.f_username.text().strip(),
            "display_name": self.f_display.text().strip(),
            "role": role_vals[self.f_role.currentIndex()],
        }
        if self._user is None:
            data["initial_password"] = self.f_password.text()
        return data
