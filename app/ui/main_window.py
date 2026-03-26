"""
主窗口：QFluentWidgets NavigationInterface + 页面路由 + 状态栏 + 主题切换
"""
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition,
    FluentIcon, Theme, setTheme, isDarkTheme,
    SubtitleLabel
)
from qfluentwidgets import FluentWindow, SplashScreen

from app.core.auth import AuthContext
from app.core.audit import write_audit
from app.utils.config_manager import ConfigManager
from version import APP_NAME, VERSION


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self._cfg = ConfigManager()
        self._ctx = AuthContext()
        self._pages: dict = {}

        self._setup_window()
        self._init_navigation()
        self._init_status_bar()

    # ── 窗口基础设置 ──────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle(APP_NAME)

        w = self._cfg.getint("app", "window_width", 1280)
        h = self._cfg.getint("app", "window_height", 800)
        self.resize(w, h)

        if self._cfg.getbool("app", "window_maximized", False):
            self.showMaximized()

        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - w) // 2,
            (screen.height() - h) // 2,
        )

    # ── 导航配置 ──────────────────────────────────────────────────

    def _init_navigation(self):
        from app.ui.pages.dashboard_page import DashboardPage
        from app.ui.pages.bom_list_page import BomListPage
        from app.ui.pages.parts_master_page import PartsMasterPage
        from app.ui.pages.audit_log_page import AuditLogPage
        from app.ui.pages.user_management_page import UserManagementPage
        from app.ui.pages.settings_page import SettingsPage

        role = self._ctx.role

        # 仪表盘 — 全部角色可见
        dashboard = DashboardPage(self)
        self.addSubInterface(dashboard, FluentIcon.HOME, "仪表盘")

        # BOM 项目 — 全部角色可见
        bom_list = BomListPage(self)
        self.addSubInterface(bom_list, FluentIcon.DOCUMENT, "BOM 项目")

        # 零件母表 — 全部角色可见（超管可编辑）
        parts = PartsMasterPage(self)
        self.addSubInterface(parts, FluentIcon.LIBRARY, "零件母表")

        # 审计日志 — 超管(全)/工程师(自己)
        if role in ("super_admin", "engineer"):
            audit = AuditLogPage(self)
            self.addSubInterface(audit, FluentIcon.HISTORY, "审计日志")

        # 底部导航项
        # 用户管理 — 仅超管
        if role == "super_admin":
            user_mgmt = UserManagementPage(self)
            self.addSubInterface(
                user_mgmt, FluentIcon.PEOPLE, "用户管理",
                position=NavigationItemPosition.BOTTOM,
            )

        # 系统设置 — 仅超管
        if role == "super_admin":
            settings = SettingsPage(self)
            self.addSubInterface(
                settings, FluentIcon.SETTING, "系统设置",
                position=NavigationItemPosition.BOTTOM,
            )

    # ── 状态栏 ────────────────────────────────────────────────────

    def _init_status_bar(self):
        from app.ui.components.status_bar_widget import StatusBarWidget
        self._status_bar = StatusBarWidget(self)
        # FluentWindow 使用 stackedWidget 作为中心控件；
        # 将状态栏作为浮动 Label 固定在底部
        self._status_bar.setParent(self)
        self._status_bar.update_user(self._ctx.user)
        self._update_status_bar_pos()

    def _update_status_bar_pos(self):
        if hasattr(self, "_status_bar"):
            bar = self._status_bar
            bar.setFixedWidth(self.width())
            bar.move(0, self.height() - bar.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_status_bar_pos()
        # 保存窗口尺寸
        self._cfg.set("app", "window_width", str(self.width()))
        self._cfg.set("app", "window_height", str(self.height()))

    # ── 关闭事件 ──────────────────────────────────────────────────

    def closeEvent(self, event):
        write_audit("LOGOUT")
        AuthContext().logout()
        event.accept()
