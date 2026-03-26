"""
登录窗口
- 用户名/密码输入
- 登录失败提示
- 首次登录后强制跳转改密对话框
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from qfluentwidgets import (
    LineEdit, PasswordLineEdit, PushButton, TitleLabel,
    SubtitleLabel, InfoBar, InfoBarPosition, FluentIcon, setTheme, Theme
)
from app.core.auth import AuthContext
from app.core.audit import write_audit
from app.models import User
from app.utils.db import get_session
from app.utils.security import verify_password


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BOM 管理系统 — 登录")
        self.setFixedSize(420, 520)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignCenter)
        root.setContentsMargins(48, 48, 48, 48)
        root.setSpacing(0)

        # 标题
        title = TitleLabel("BOM 管理系统")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        sub = SubtitleLabel("请登录以继续")
        sub.setAlignment(Qt.AlignCenter)
        sub.setObjectName("loginSubtitle")
        root.addSpacing(8)
        root.addWidget(sub)
        root.addSpacing(36)

        # 用户名
        self.username_edit = LineEdit()
        self.username_edit.setPlaceholderText("用户名")
        self.username_edit.setFixedHeight(40)
        root.addWidget(self.username_edit)
        root.addSpacing(12)

        # 密码
        self.password_edit = PasswordLineEdit()
        self.password_edit.setPlaceholderText("密码")
        self.password_edit.setFixedHeight(40)
        self.password_edit.returnPressed.connect(self._on_login)
        root.addWidget(self.password_edit)
        root.addSpacing(24)

        # 登录按钮
        self.login_btn = PushButton("登 录")
        self.login_btn.setFixedHeight(40)
        self.login_btn.clicked.connect(self._on_login)
        root.addWidget(self.login_btn)

        root.addStretch()

        # 底部版本信息
        from version import VERSION, APP_NAME
        footer = QLabel(f"{APP_NAME}  v{VERSION}")
        footer.setAlignment(Qt.AlignCenter)
        footer.setObjectName("loginFooter")
        root.addWidget(footer)

    def _on_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            InfoBar.warning(
                title="请填写完整",
                content="用户名和密码不能为空",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self,
            )
            return

        with get_session() as session:
            user: User = session.query(User).filter_by(
                username=username, is_deleted=0
            ).first()

        if user is None or not verify_password(password, user.password_hash):
            write_audit(
                "LOGIN_FAIL",
                detail=f"用户名: {username}",
                operator_name=username,
            )
            InfoBar.error(
                title="登录失败",
                content="用户名或密码错误",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            self.password_edit.clear()
            return

        # 登录成功
        from datetime import datetime, timezone
        with get_session() as session:
            u = session.get(User, user.id)
            u.last_login_at = datetime.now(timezone.utc)
            session.commit()

        AuthContext().login(user)
        write_audit("LOGIN_SUCCESS", operator_id=user.id, operator_name=user.display_name)

        # 首次登录强制改密
        if user.must_change_pwd:
            from app.ui.dialogs.change_password_dialog import ChangePasswordDialog
            dlg = ChangePasswordDialog(user, force=True, parent=self)
            if not dlg.exec():
                AuthContext().logout()
                return

        self._open_main_window()

    def _open_main_window(self):
        from app.ui.main_window import MainWindow
        self._main = MainWindow()
        self._main.show()
        self.close()
