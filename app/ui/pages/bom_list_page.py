"""
BOM 项目列表页面
- 搜索/筛选
- 表格展示项目列表
- 新建 / 打开编辑器 / 归档 / 删除
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from qfluentwidgets import (
    TitleLabel, CaptionLabel, SearchLineEdit,
    PrimaryPushButton, FluentIcon,
    InfoBar, InfoBarPosition, TableWidget,
)
from app.core.auth import AuthContext
from app.core.rbac import PermissionDenied
from app.services import bom_service

_STATUS_LABEL = {"active": "进行中", "archived": "已归档"}


class BomListPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BomListPage")
        self._rows: list[dict] = []
        self._loading = False
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 36, 36, 20)
        root.setSpacing(12)

        root.addWidget(TitleLabel("BOM 项目"))

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self._search = SearchLineEdit(self)
        self._search.setPlaceholderText("搜索 BOM 编号 / 客户零件号 / 项目名称")
        self._search.setFixedWidth(360)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(400)
        self._search_timer.timeout.connect(lambda: self._load(self._search.text()))
        self._search.textChanged.connect(lambda _: self._search_timer.start())
        toolbar.addWidget(self._search)
        toolbar.addStretch()

        role = AuthContext().role
        if role in ("super_admin", "engineer"):
            btn_new = PrimaryPushButton(FluentIcon.ADD, "新建项目", self)
            btn_new.clicked.connect(self._on_new)
            toolbar.addWidget(btn_new)
        root.addLayout(toolbar)

        # 表格（无"操作"列，改用右键菜单）
        cols = ["BOM 编号", "客户零件号", "项目名称", "当前版本", "建立日期", "更新日期", "状态"]
        self._table = TableWidget(self)
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        for i in [0, 1, 3, 4, 5, 6]:
            hh.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_row_double_clicked)
        root.addWidget(self._table)

        self._count_label = CaptionLabel("共 0 个项目")
        root.addWidget(self._count_label)

    def _load(self, keyword: str = ""):
        if self._loading:
            return
        self._loading = True
        try:
            projects = bom_service.search_projects(keyword)
            self._rows = [
                {
                    "id": p.id,
                    "bom_number": p.bom_number or "",
                    "customer_part_number": p.customer_part_number or "",
                    "project_name": p.project_name or "",
                    "current_version": p.current_version or "",
                    "established_date": str(p.established_date) if p.established_date else "",
                    "updated_date": str(p.updated_date) if p.updated_date else "",
                    "status": p.status or "active",
                }
                for p in projects
            ]
            self._render()
        except Exception:
            pass
        finally:
            self._loading = False

    def _render(self):
        tbl = self._table
        tbl.setUpdatesEnabled(False)
        tbl.blockSignals(True)
        tbl.clearContents()
        tbl.setRowCount(len(self._rows))
        for row, d in enumerate(self._rows):
            values = [
                d["bom_number"],
                d["customer_part_number"],
                d["project_name"],
                d["current_version"],
                d["established_date"],
                d["updated_date"],
                _STATUS_LABEL.get(d["status"], d["status"]),
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                tbl.setItem(row, col, item)
        tbl.blockSignals(False)
        tbl.setUpdatesEnabled(True)
        self._count_label.setText(f"共 {len(self._rows)} 个项目")

    def _on_context_menu(self, pos):
        index = self._table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        if row >= len(self._rows):
            return
        d = self._rows[row]
        role = AuthContext().role
        is_admin = role == "super_admin"
        can_edit = role in ("super_admin", "engineer")

        menu = QMenu(self)
        act_open = QAction("打开编辑器", self)
        act_open.setEnabled(can_edit)
        act_open.triggered.connect(lambda: self._open_editor(d["id"]))
        menu.addAction(act_open)

        menu.addSeparator()

        act_archive = QAction("归档项目", self)
        act_archive.setEnabled(is_admin and d["status"] == "active")
        act_archive.triggered.connect(lambda: self._on_archive(d["id"]))
        menu.addAction(act_archive)

        act_del = QAction("删除项目", self)
        act_del.setEnabled(is_admin)
        act_del.triggered.connect(lambda: self._on_delete(d["id"]))
        menu.addAction(act_del)

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_row_double_clicked(self, index):
        row = index.row()
        if row < len(self._rows):
            self._open_editor(self._rows[row]["id"])

    def _on_new(self):
        from app.ui.dialogs.add_bom_dialog import AddBomDialog
        dlg = AddBomDialog(parent=self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                proj = bom_service.create_project(**data)
                self._load(self._search.text())
                InfoBar.success("成功", f"BOM 项目 {data['bom_number']} 已创建",
                                parent=self, position=InfoBarPosition.TOP, duration=2500)
                self._open_editor(proj.id)
            except (ValueError, PermissionDenied) as e:
                InfoBar.error("失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)

    def _open_editor(self, project_id: str):
        from app.ui.pages.bom_editor_page import BomEditorPage
        main_win = self.window()
        if not hasattr(main_win, "_editor_pages"):
            main_win._editor_pages = {}

        if project_id not in main_win._editor_pages:
            proj = bom_service.get_project(project_id)
            if not proj:
                return
            editor = BomEditorPage(project_id, main_win)
            main_win._editor_pages[project_id] = editor
            main_win.addSubInterface(
                editor, FluentIcon.DOCUMENT,
                f"BOM: {proj.bom_number}",
            )
        main_win.switchTo(main_win._editor_pages[project_id])

    def _on_archive(self, project_id: str):
        from qfluentwidgets import MessageBox
        box = MessageBox("归档确认", "归档后该项目将不可编辑，是否继续？", self)
        if box.exec():
            try:
                bom_service.archive_project(project_id)
                self._load(self._search.text())
                InfoBar.success("已归档", "项目已归档",
                                parent=self, position=InfoBarPosition.TOP, duration=2500)
            except (ValueError, PermissionDenied) as e:
                InfoBar.error("失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)

    def _on_delete(self, project_id: str):
        from qfluentwidgets import MessageBox
        box = MessageBox("确认删除", "项目将被软删除，BOM 数据仍可在审计日志中追溯，是否继续？", self)
        if box.exec():
            try:
                bom_service.soft_delete_project(project_id)
                self._load(self._search.text())
                InfoBar.success("已删除", "项目已删除",
                                parent=self, position=InfoBarPosition.TOP, duration=2500)
            except (ValueError, PermissionDenied) as e:
                InfoBar.error("失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)
