"""
BOM 变更历史页面 — 变更履历表 + 版本快照 + Diff 对比高亮
"""
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QTabWidget,
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, CaptionLabel, TableWidget, PushButton, FluentIcon,
)
from app.services import bom_service


class BomHistoryPage(QWidget):
    def __init__(self, project_id: str, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._logs = []
        self.setObjectName(f"BomHistory_{project_id}")
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 24, 36, 20)
        root.setSpacing(10)

        proj = bom_service.get_project(self._project_id)
        title = f"变更历史 — {proj.bom_number}" if proj else "变更历史"
        root.addWidget(TitleLabel(title))

        # 顶部提示
        root.addWidget(CaptionLabel("点击左侧变更记录查看快照；选中两行后点击「对比差异」查看 Diff"))

        splitter = QSplitter(Qt.Horizontal)

        # ── 左：变更履历表 ──
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 8, 0)
        ll.setSpacing(6)

        ll.addWidget(CaptionLabel("变更履历（最新在上）"))
        self._log_table = TableWidget(left)
        self._log_table.setColumnCount(6)
        self._log_table.setHorizontalHeaderLabels(
            ["序目", "变更原因", "变更前版本", "变更后版本", "变更人", "日期"]
        )
        hh = self._log_table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.Fixed); self._log_table.setColumnWidth(0, 44)
        hh.setSectionResizeMode(2, QHeaderView.Fixed); self._log_table.setColumnWidth(2, 72)
        hh.setSectionResizeMode(3, QHeaderView.Fixed); self._log_table.setColumnWidth(3, 72)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self._log_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._log_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._log_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self._log_table.verticalHeader().setVisible(False)
        self._log_table.currentRowChanged.connect(self._on_log_selected)
        ll.addWidget(self._log_table)

        btn_diff = PushButton(FluentIcon.SEARCH, "对比选中两个版本的差异", left)
        btn_diff.clicked.connect(self._on_diff)
        ll.addWidget(btn_diff)
        splitter.addWidget(left)

        # ── 右：Tab（快照 + Diff）──
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 0, 0, 0)

        self._tabs = QTabWidget(right)

        # Tab 1：版本快照
        snap_widget = QWidget()
        snap_layout = QVBoxLayout(snap_widget)
        snap_layout.setContentsMargins(0, 8, 0, 0)
        self._snap_table = TableWidget(snap_widget)
        self._snap_table.setColumnCount(7)
        self._snap_table.setHorizontalHeaderLabels(
            ["层级", "零件图号", "零件名称", "规格/材料", "单位", "用量", "备注"]
        )
        self._snap_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i in [0, 4, 5]:
            self._snap_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self._snap_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._snap_table.verticalHeader().setVisible(False)
        self._snap_table.setAlternatingRowColors(True)
        snap_layout.addWidget(self._snap_table)
        self._tabs.addTab(snap_widget, "版本快照")

        # Tab 2：Diff 对比
        from app.ui.components.diff_viewer_widget import DiffViewerWidget
        self._diff_viewer = DiffViewerWidget(self)
        self._tabs.addTab(self._diff_viewer, "差异对比")

        rl.addWidget(self._tabs)
        splitter.addWidget(right)

        splitter.setSizes([380, 660])
        root.addWidget(splitter, stretch=1)

    def _load(self):
        self._logs = bom_service.get_change_logs(self._project_id)
        self._log_table.setRowCount(0)
        for log in self._logs:
            row = self._log_table.rowCount()
            self._log_table.insertRow(row)
            for col, val in enumerate([
                str(log.sequence),
                log.change_reason,
                log.previous_version or "—",
                log.new_version,
                log.changed_by_name or "系统",
                log.change_date,
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self._log_table.setItem(row, col, item)

    def _on_log_selected(self, row: int):
        if row < 0 or row >= len(self._logs):
            return
        log = self._logs[row]
        items = bom_service.restore_snapshot(log)
        self._snap_table.setRowCount(0)
        for d in items:
            r = self._snap_table.rowCount()
            self._snap_table.insertRow(r)
            snap = {}
            ps = d.get("part_snapshot")
            if ps:
                try:
                    snap = json.loads(ps) if isinstance(ps, str) else ps
                except Exception:
                    pass
            for col, val in enumerate([
                str(d.get("level", "")),
                d.get("part_number", ""),
                snap.get("name", ""),
                snap.get("spec_material", ""),
                snap.get("unit", ""),
                str(d.get("quantity", "")),
                d.get("notes", ""),
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self._snap_table.setItem(r, col, item)
        self._tabs.setCurrentIndex(0)

    def _on_diff(self):
        selected = self._log_table.selectionModel().selectedRows()
        if len(selected) != 2:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.warning("提示", "请在左侧选中恰好两行进行差异对比",
                            parent=self, position=InfoBarPosition.TOP, duration=2500)
            return

        rows = sorted(r.row() for r in selected)
        # rows[0] 是较新的（序号大），rows[1] 是较旧的
        # 但 _logs 是 desc 顺序，所以 rows[0] 对应更新的版本
        log_new = self._logs[rows[0]]
        log_old = self._logs[rows[1]]

        self._diff_viewer.compare(log_old.bom_snapshot, log_new.bom_snapshot)
        self._tabs.setCurrentIndex(1)
