"""
零件母表页面
- 搜索/筛选（防抖）
- 表格展示（纯文字行，列可见性自定义）
- 右键上下文菜单：编辑/删除（超管）
- 工具栏：新增 / 导入 Excel / 导出 Excel
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu,
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QAction
from qfluentwidgets import (
    TitleLabel, CaptionLabel, SearchLineEdit, PrimaryPushButton,
    PushButton, FluentIcon, InfoBar, InfoBarPosition,
    TableWidget,
)
from app.core.auth import AuthContext
from app.core.rbac import PermissionDenied
from app.services import part_service

_ALL_COLS = ["零件图号", "版本", "零件标准", "零件名称", "规格/材料", "单位", "用量", "备注"]


class PartsMasterPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PartsMasterPage")
        self._is_admin = AuthContext().is_super_admin()
        self._hidden_cols: set[str] = set()
        self._loading = False
        # 缓存为纯 dict，避免 detached 对象访问问题
        self._rows: list[dict] = []
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 36, 36, 20)
        root.setSpacing(12)
        root.addWidget(TitleLabel("零件母表"))

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._search = SearchLineEdit(self)
        self._search.setPlaceholderText("搜索零件图号 / 名称 / 规格")
        self._search.setFixedWidth(320)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(400)
        self._search_timer.timeout.connect(lambda: self._load(self._search.text()))
        self._search.textChanged.connect(lambda _: self._search_timer.start())
        toolbar.addWidget(self._search)
        toolbar.addStretch()

        if self._is_admin:
            btn_add = PrimaryPushButton(FluentIcon.ADD, "新增零件", self)
            btn_add.clicked.connect(self._on_add)
            toolbar.addWidget(btn_add)

            btn_import = PushButton(FluentIcon.DOWNLOAD, "导入 Excel", self)
            btn_import.clicked.connect(self._on_import)
            toolbar.addWidget(btn_import)

        btn_export = PushButton(FluentIcon.SHARE, "导出 Excel", self)
        btn_export.clicked.connect(self._on_export)
        toolbar.addWidget(btn_export)
        root.addLayout(toolbar)

        # 表格（纯文字，无 CellWidget）
        self._table = TableWidget(self)
        self._table.setColumnCount(len(_ALL_COLS))
        self._table.setHorizontalHeaderLabels(_ALL_COLS)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        for i in [0, 1, 2, 5, 6]:
            hh.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)

        # 右键菜单（超管功能）
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_row_ctx_menu)

        # 表头右键：列可见性
        hh.setContextMenuPolicy(Qt.CustomContextMenu)
        hh.customContextMenuRequested.connect(self._on_header_ctx_menu)

        root.addWidget(self._table)

        self._count_label = CaptionLabel("共 0 条")
        root.addWidget(self._count_label)

    # ── 右键：行操作菜单 ───────────────────────────────────────────

    def _on_row_ctx_menu(self, pos: QPoint):
        row = self._table.rowAt(pos.y())
        if row < 0 or row >= len(self._rows):
            return
        menu = QMenu(self)
        if self._is_admin:
            act_edit = QAction(FluentIcon.EDIT.icon(), "编辑", menu)
            act_edit.triggered.connect(lambda: self._on_edit(self._rows[row]["id"]))
            menu.addAction(act_edit)
            act_del = QAction(FluentIcon.DELETE.icon(), "删除", menu)
            act_del.triggered.connect(lambda: self._on_delete(self._rows[row]["id"]))
            menu.addAction(act_del)
        else:
            act_view = QAction("（只读，无操作权限）", menu)
            act_view.setEnabled(False)
            menu.addAction(act_view)
        menu.exec(self._table.viewport().mapToGlobal(pos))

    # ── 右键：列可见性菜单 ─────────────────────────────────────────

    def _on_header_ctx_menu(self, pos: QPoint):
        menu = QMenu(self)
        for col_name in _ALL_COLS:
            if col_name == "零件图号":
                continue
            action = QAction(col_name, menu)
            action.setCheckable(True)
            action.setChecked(col_name not in self._hidden_cols)
            action.triggered.connect(lambda checked, cn=col_name: self._toggle_col(cn, checked))
            menu.addAction(action)
        menu.exec(self._table.horizontalHeader().mapToGlobal(pos))

    def _toggle_col(self, col_name: str, visible: bool):
        idx = _ALL_COLS.index(col_name)
        if visible:
            self._hidden_cols.discard(col_name)
            self._table.showColumn(idx)
        else:
            self._hidden_cols.add(col_name)
            self._table.hideColumn(idx)

    # ── 数据加载与渲染 ─────────────────────────────────────────────

    def _load(self, keyword: str = ""):
        if self._loading:
            return
        self._loading = True
        try:
            parts = part_service.search_parts(keyword)
            # 立即转为纯 dict，脱离 SQLAlchemy session
            self._rows = [
                {
                    "id":             p.id,
                    "part_number":    p.part_number,
                    "version":        p.version or "",
                    "standard_level": p.standard_level or "",
                    "name":           p.name or "",
                    "spec_material":  p.spec_material or "",
                    "unit":           p.unit or "",
                    "default_qty":    str(p.default_qty) if p.default_qty is not None else "1.0",
                    "notes":          p.notes or "",
                }
                for p in parts
            ]
            self._render()
        except Exception:
            pass
        finally:
            self._loading = False

    def _render(self):
        tbl = self._table
        tbl.setUpdatesEnabled(False)
        tbl.clearContents()
        tbl.setRowCount(len(self._rows))

        for row, d in enumerate(self._rows):
            values = [
                d["part_number"], d["version"], d["standard_level"],
                d["name"], d["spec_material"], d["unit"],
                d["default_qty"], d["notes"],
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                tbl.setItem(row, col, item)

        # 恢复隐藏列
        for col_name in self._hidden_cols:
            if col_name in _ALL_COLS:
                tbl.hideColumn(_ALL_COLS.index(col_name))

        tbl.setUpdatesEnabled(True)
        self._count_label.setText(f"共 {len(self._rows)} 条")

    # ── 操作 ───────────────────────────────────────────────────────

    def _on_add(self):
        from app.ui.dialogs.add_part_dialog import AddPartDialog
        dlg = AddPartDialog(parent=self.window())
        if dlg.exec():
            data = dlg.get_data()
            try:
                part_service.create_part(**data)
                self._load(self._search.text())
                InfoBar.success("成功", f"零件 {data['part_number']} 已新增",
                                parent=self, position=InfoBarPosition.TOP, duration=2500)
            except (ValueError, PermissionDenied) as e:
                InfoBar.error("失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)

    def _on_edit(self, part_id: int):
        from app.ui.dialogs.add_part_dialog import AddPartDialog
        from app.utils.db import get_session
        from app.models import PartsMaster
        with get_session() as s:
            part = s.get(PartsMaster, part_id)
        if not part:
            return
        dlg = AddPartDialog(part=part, parent=self.window())
        if dlg.exec():
            data = dlg.get_data()
            data.pop("part_number")
            try:
                part_service.update_part(part_id, **data)
                self._load(self._search.text())
                InfoBar.success("成功", "零件信息已更新",
                                parent=self, position=InfoBarPosition.TOP, duration=2500)
            except (ValueError, PermissionDenied) as e:
                InfoBar.error("失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)

    def _on_delete(self, part_id: int):
        from qfluentwidgets import MessageBox
        box = MessageBox("确认删除", "该零件将被软删除，可在审计日志中追溯，是否继续？",
                         self.window())
        if box.exec():
            try:
                part_service.soft_delete_part(part_id)
                self._load(self._search.text())
                InfoBar.success("已删除", "零件已软删除",
                                parent=self, position=InfoBarPosition.TOP, duration=2500)
            except (ValueError, PermissionDenied) as e:
                InfoBar.error("失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)

    def _on_import(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "选择零件母表 Excel", "",
            "Excel 文件 (*.xlsx *.xls *.xlsm)"
        )
        if not path:
            return
        try:
            added, skipped, errors = part_service.import_parts_from_excel(path)
            msg = f"新增 {added} 条"
            if skipped:
                msg += f"，跳过重复 {skipped} 条"
            self._load(self._search.text())
            if errors:
                InfoBar.warning("导入完成", msg + "；" + errors[0],
                                parent=self, position=InfoBarPosition.TOP, duration=5000)
            else:
                InfoBar.success("导入成功", msg,
                                parent=self, position=InfoBarPosition.TOP, duration=3000)
        except Exception as e:
            InfoBar.error("导入失败", str(e), parent=self,
                          position=InfoBarPosition.TOP, duration=4000)

    def _on_export(self):
        from PySide6.QtWidgets import QFileDialog
        from app.utils.config_manager import ConfigManager
        import os
        default_dir = ConfigManager().get("export", "default_export_dir", "exports/")
        os.makedirs(default_dir, exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(
            self, "导出零件母表", f"{default_dir}零部件总览表.xlsx",
            "Excel 文件 (*.xlsx)"
        )
        if path:
            try:
                part_service.export_parts_to_excel(path)
                InfoBar.success("导出成功", f"已保存至 {path}",
                                parent=self, position=InfoBarPosition.TOP, duration=3000)
            except Exception as e:
                InfoBar.error("导出失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)
