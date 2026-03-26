"""
用户管理页面（仅超管可见）
- 用户列表表格
- 新增用户 / 编辑角色与显示名
- 重置密码
- 软删除用户
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, CaptionLabel, PrimaryPushButton, ToolButton,
    FluentIcon, InfoBar, InfoBarPosition, TableWidget,
)
from app.core.auth import AuthContext
from app.core.rbac import PermissionDenied
from app.services import user_service

_ROLE_DISPLAY = {
    "super_admin": "🔴 超级管理员",
    "engineer":    "🔵 工程师",
    "viewer":      "🟢 查看者",
}


class UserManagementPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("UserManagementPage")
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 36, 36, 20)
        root.setSpacing(12)

        root.addWidget(TitleLabel("用户管理"))

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        btn_add = PrimaryPushButton(FluentIcon.ADD, "新增用户", self)
        btn_add.clicked.connect(self._on_add)
        toolbar.addWidget(btn_add)
        root.addLayout(toolbar)

        cols = ["用户名", "显示名称", "角色", "最后登录", "操作"]
        self._table = TableWidget(self)
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self._table.setColumnWidth(4, 150)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        root.addWidget(self._table)

        self._count_label = CaptionLabel("共 0 位用户")
        root.addWidget(self._count_label)

    def _load(self):
        self._users = user_service.get_all_users()
        self._render()

    def _render(self):
        self._table.setRowCount(0)
        current_id = AuthContext().user.id if AuthContext().user else None

        for u in self._users:
            row = self._table.rowCount()
            self._table.insertRow(row)

            last_login = u.last_login_at.strftime("%Y-%m-%d %H:%M") if u.last_login_at else "从未"
            for col, val in enumerate([
                u.username,
                u.display_name,
                _ROLE_DISPLAY.get(u.role, u.role),
                last_login,
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self._table.setItem(row, col, item)

            # 操作列
            cell = QWidget()
            lay = QHBoxLayout(cell)
            lay.setContentsMargins(4, 2, 4, 2)
            lay.setSpacing(4)

            btn_edit = ToolButton(FluentIcon.EDIT, cell)
            btn_edit.setFixedSize(28, 28)
            btn_edit.setToolTip("编辑用户")
            btn_edit.clicked.connect(lambda _, uid=u.id: self._on_edit(uid))

            btn_pwd = ToolButton(FluentIcon.VPN, cell)
            btn_pwd.setFixedSize(28, 28)
            btn_pwd.setToolTip("重置密码")
            btn_pwd.clicked.connect(lambda _, uid=u.id: self._on_reset_pwd(uid))

            btn_del = ToolButton(FluentIcon.DELETE, cell)
            btn_del.setFixedSize(28, 28)
            btn_del.setToolTip("删除用户")
            btn_del.setEnabled(u.id != current_id)  # 不能删自己
            btn_del.clicked.connect(lambda _, uid=u.id: self._on_delete(uid))

            lay.addWidget(btn_edit)
            lay.addWidget(btn_pwd)
            lay.addWidget(btn_del)
            lay.addStretch()
            self._table.setCellWidget(row, 4, cell)

        self._count_label.setText(f"共 {len(self._users)} 位用户")

    def _on_add(self):
        from app.ui.dialogs.add_user_dialog import AddUserDialog
        dlg = AddUserDialog(parent=self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                user_service.create_user(**data)
                self._load()
                InfoBar.success("成功", f"用户 {data['username']} 已创建",
                                parent=self, position=InfoBarPosition.TOP, duration=2500)
            except (ValueError, PermissionDenied) as e:
                InfoBar.error("失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)

    def _on_edit(self, user_id: str):
        from app.ui.dialogs.add_user_dialog import AddUserDialog
        u = user_service.get_user_by_id(user_id)
        if not u:
            return
        dlg = AddUserDialog(user=u, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                user_service.update_user(
                    user_id,
                    display_name=data["display_name"],
                    role=data["role"],
                )
                self._load()
                InfoBar.success("成功", "用户信息已更新",
                                parent=self, position=InfoBarPosition.TOP, duration=2500)
            except (ValueError, PermissionDenied) as e:
                InfoBar.error("失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)

    def _on_reset_pwd(self, user_id: str):
        from app.ui.dialogs.reset_password_dialog import ResetPasswordDialog
        u = user_service.get_user_by_id(user_id)
        if not u:
            return
        dlg = ResetPasswordDialog(user=u, parent=self)
        if dlg.exec():
            InfoBar.success("成功", f"用户 {u.username} 的密码已重置",
                            parent=self, position=InfoBarPosition.TOP, duration=2500)

    def _on_delete(self, user_id: str):
        from qfluentwidgets import MessageBox
        u = user_service.get_user_by_id(user_id)
        if not u:
            return
        box = MessageBox("确认删除", f"将软删除用户 [{u.username}]，该用户将无法登录，是否继续？", self)
        if box.exec():
            try:
                user_service.soft_delete_user(user_id)
                self._load()
                InfoBar.success("已删除", f"用户 {u.username} 已被禁用",
                                parent=self, position=InfoBarPosition.TOP, duration=2500)
            except (ValueError, PermissionDenied) as e:
                InfoBar.error("失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)
