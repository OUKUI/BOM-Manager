"""
仪表盘页面
- 顶部：欢迎语 + 当前用户
- 统计卡片：项目总数 / 零件总数 / 本周变更次数 / 活跃项目数
- 最近编辑的 BOM 项目列表（5条）
- 快捷入口按钮
"""
from datetime import datetime, timedelta, timezone
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGridLayout,
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    ScrollArea, TitleLabel, SubtitleLabel, CaptionLabel,
    PrimaryPushButton, PushButton, FluentIcon,
    TableWidget, CardWidget,
)
from app.core.auth import AuthContext
from app.utils.db import get_session
from app.models import BomProject, PartsMaster, BomChangeLog, AuditLog


class _StatCard(CardWidget):
    def __init__(self, icon, label: str, value: str, color: str = None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        top = QHBoxLayout()
        from qfluentwidgets import IconWidget
        ic = IconWidget(icon, self)
        ic.setFixedSize(28, 28)
        top.addWidget(ic)
        top.addStretch()
        layout.addLayout(top)

        val_lbl = TitleLabel(value, self)
        if color:
            val_lbl.setStyleSheet(f"color:{color};")
        layout.addWidget(val_lbl)

        lbl = CaptionLabel(label, self)
        layout.addWidget(lbl)

        self.setFixedHeight(110)

    def set_value(self, value: str):
        # 找到 TitleLabel 子控件更新数值
        for child in self.findChildren(TitleLabel):
            child.setText(value)
            break


class DashboardPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DashboardPage")
        self.setWidgetResizable(True)
        self._build_ui()
        self._load_stats()

    def _build_ui(self):
        root_widget = QWidget()
        root = QVBoxLayout(root_widget)
        root.setContentsMargins(36, 36, 36, 36)
        root.setSpacing(20)
        root.setAlignment(Qt.AlignTop)

        # ── 欢迎语 ──
        ctx = AuthContext()
        user_name = ctx.user.display_name if ctx.user else ""
        root.addWidget(TitleLabel("仪表盘"))
        root.addWidget(SubtitleLabel(f"欢迎回来，{user_name} 👋"))

        # ── 统计卡片行 ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self._card_projects  = _StatCard(FluentIcon.DOCUMENT,  "BOM 项目总数",  "—", parent=self)
        self._card_parts     = _StatCard(FluentIcon.LIBRARY,   "零件母表条目",  "—", parent=self)
        self._card_changes   = _StatCard(FluentIcon.HISTORY,   "本周变更次数",  "—", "#1976D2", parent=self)
        self._card_active    = _StatCard(FluentIcon.ACCEPT,    "进行中项目",    "—", "#2E7D32", parent=self)

        for card in [self._card_projects, self._card_parts,
                     self._card_changes, self._card_active]:
            cards_layout.addWidget(card)
        root.addLayout(cards_layout)

        # ── 最近编辑的项目 ──
        root.addWidget(SubtitleLabel("最近编辑的项目"))

        self._recent_table = TableWidget(self)
        self._recent_table.setColumnCount(5)
        self._recent_table.setHorizontalHeaderLabels(
            ["BOM 编号", "客户零件号", "当前版本", "更新日期", "状态"]
        )
        hh = self._recent_table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        for i in [2, 3, 4]:
            hh.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self._recent_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._recent_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._recent_table.verticalHeader().setVisible(False)
        self._recent_table.setFixedHeight(220)
        self._recent_table.doubleClicked.connect(self._on_open_project)
        root.addWidget(self._recent_table)

        # ── 快捷入口 ──
        root.addWidget(SubtitleLabel("快捷入口"))
        quick_row = QHBoxLayout()
        quick_row.setSpacing(12)

        btn_new_bom = PrimaryPushButton(FluentIcon.ADD, "新建 BOM 项目", self)
        btn_new_bom.clicked.connect(self._quick_new_bom)
        quick_row.addWidget(btn_new_bom)

        btn_parts = PushButton(FluentIcon.LIBRARY, "零件母表", self)
        btn_parts.clicked.connect(lambda: self._navigate("PartsMasterPage"))
        quick_row.addWidget(btn_parts)

        btn_logs = PushButton(FluentIcon.HISTORY, "审计日志", self)
        btn_logs.clicked.connect(lambda: self._navigate("AuditLogPage"))
        quick_row.addWidget(btn_logs)

        quick_row.addStretch()
        root.addLayout(quick_row)

        self.setWidget(root_widget)

    def _load_stats(self):
        with get_session() as s:
            n_projects = s.query(BomProject).filter_by(is_deleted=0).count()
            n_parts    = s.query(PartsMaster).filter_by(is_deleted=0).count()
            n_active   = s.query(BomProject).filter_by(is_deleted=0, status="active").count()

            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            n_changes = s.query(BomChangeLog).filter(
                BomChangeLog.change_date >= week_ago.strftime("%Y-%m-%d")
            ).count()

            recent = (
                s.query(BomProject)
                .filter_by(is_deleted=0)
                .order_by(BomProject.updated_at.desc())
                .limit(5)
                .all()
            )

        self._card_projects.set_value(str(n_projects))
        self._card_parts.set_value(str(n_parts))
        self._card_changes.set_value(str(n_changes))
        self._card_active.set_value(str(n_active))

        self._recent_table.setRowCount(0)
        self._recent_projects = recent
        _STATUS = {"active": "进行中", "archived": "已归档"}
        for p in recent:
            row = self._recent_table.rowCount()
            self._recent_table.insertRow(row)
            for col, val in enumerate([
                p.bom_number,
                p.customer_part_number or "",
                p.current_version,
                p.updated_date or "",
                _STATUS.get(p.status, p.status),
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self._recent_table.setItem(row, col, item)

    def _on_open_project(self, index):
        row = index.row()
        if row < len(self._recent_projects):
            proj = self._recent_projects[row]
            self._open_editor(proj.id)

    def _open_editor(self, project_id: str):
        from app.ui.pages.bom_editor_page import BomEditorPage
        from app.services.bom_service import get_project
        main_win = self.window()
        if not hasattr(main_win, "_editor_pages"):
            main_win._editor_pages = {}
        if project_id not in main_win._editor_pages:
            proj = get_project(project_id)
            if not proj:
                return
            editor = BomEditorPage(project_id, main_win)
            main_win._editor_pages[project_id] = editor
            main_win.addSubInterface(editor, FluentIcon.DOCUMENT, f"BOM: {proj.bom_number}")
        main_win.switchTo(main_win._editor_pages[project_id])

    def _quick_new_bom(self):
        from app.ui.dialogs.add_bom_dialog import AddBomDialog
        from app.services.bom_service import create_project
        from app.core.rbac import PermissionDenied
        from qfluentwidgets import InfoBar, InfoBarPosition
        dlg = AddBomDialog(parent=self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                proj = create_project(**data)
                self._load_stats()
                InfoBar.success("成功", f"项目 {data['bom_number']} 已创建",
                                parent=self, position=InfoBarPosition.TOP, duration=2500)
                self._open_editor(proj.id)
            except (ValueError, PermissionDenied) as e:
                InfoBar.error("失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)

    def _navigate(self, page_object_name: str):
        main_win = self.window()
        for child in main_win.findChildren(QWidget):
            if child.objectName() == page_object_name:
                main_win.switchTo(child)
                return
