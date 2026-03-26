"""
底部状态栏组件：显示当前用户、角色、系统提示
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from qfluentwidgets import CaptionLabel, isDarkTheme

_ROLE_LABELS = {
    "super_admin": "🔴 超级管理员",
    "engineer":    "🔵 工程师",
    "viewer":      "🟢 查看者",
}


class StatusBarWidget(QWidget):
    HEIGHT = 28

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self.HEIGHT)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(16)

        self._user_label = CaptionLabel("未登录")
        self._role_label = CaptionLabel("")
        self._hint_label = CaptionLabel("")

        layout.addWidget(self._user_label)
        layout.addWidget(self._role_label)
        layout.addStretch()
        layout.addWidget(self._hint_label)

        self._apply_style()

    def _apply_style(self):
        bg = "rgba(32,32,32,200)" if isDarkTheme() else "rgba(240,240,240,200)"
        self.setStyleSheet(f"StatusBarWidget {{ background: {bg}; }}")

    def update_user(self, user):
        if user:
            self._user_label.setText(f"👤 {user.display_name} ({user.username})")
            self._role_label.setText(_ROLE_LABELS.get(user.role, user.role))
        else:
            self._user_label.setText("未登录")
            self._role_label.setText("")

    def set_hint(self, text: str):
        self._hint_label.setText(text)
