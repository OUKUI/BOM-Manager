"""
BOM 编辑器页面
- 顶部：项目头部信息（BOM编号/客户零件号/版本/日期）
- 中部：BomTreeWidget 树形表格
- 底部工具栏：保存、导出、历史版本
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, CaptionLabel,
    PrimaryPushButton, PushButton, ToolButton,
    FluentIcon, InfoBar, InfoBarPosition,
)
from app.core.auth import AuthContext
from app.core.rbac import PermissionDenied
from app.services import bom_service
from app.ui.components.bom_tree_widget import BomTreeWidget


class BomEditorPage(QWidget):
    def __init__(self, project_id: str, parent=None):
        super().__init__(parent)
        self._project_id = project_id
        self._dirty = False
        self.setObjectName(f"BomEditor_{project_id}")
        self._load_project()
        self._build_ui()
        self._load_items()

    def _load_project(self):
        self._proj = bom_service.get_project(self._project_id)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 24, 36, 20)
        root.setSpacing(10)

        # ── 标题行 ──
        title_row = QHBoxLayout()
        self._title_label = TitleLabel(
            f"BOM 编辑器 — {self._proj.bom_number}" if self._proj else "BOM 编辑器"
        )
        title_row.addWidget(self._title_label)
        title_row.addStretch()

        btn_save = PrimaryPushButton(FluentIcon.SAVE, "保存", self)
        btn_save.clicked.connect(self._on_save)
        title_row.addWidget(btn_save)

        btn_import = PushButton(FluentIcon.DOWNLOAD, "导入 Excel", self)
        btn_import.clicked.connect(self._on_import)
        title_row.addWidget(btn_import)

        btn_export = PushButton(FluentIcon.SHARE, "导出 Excel", self)
        btn_export.clicked.connect(self._on_export)
        title_row.addWidget(btn_export)

        btn_history = PushButton(FluentIcon.HISTORY, "变更历史", self)
        btn_history.clicked.connect(self._on_history)
        title_row.addWidget(btn_history)

        root.addLayout(title_row)

        # ── 头部信息卡片 ──
        info_layout = QHBoxLayout()
        info_layout.setSpacing(32)

        def _info(label: str, value: str) -> QWidget:
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(2)
            lbl = CaptionLabel(label)
            val = SubtitleLabel(value or "—")
            val.setObjectName("infoValue")
            l.addWidget(lbl)
            l.addWidget(val)
            return w, val

        p = self._proj

        w1, self._lbl_bom_no     = _info("BOM 编号",   p.bom_number if p else "")
        w2, self._lbl_cust_pn    = _info("客户零件号", p.customer_part_number if p else "")
        w3, self._lbl_version    = _info("当前版本",   p.current_version if p else "")
        w4, self._lbl_est_date   = _info("建立日期",   p.established_date if p else "")
        w5, self._lbl_upd_date   = _info("更新日期",   p.updated_date if p else "")

        for w in [w1, w2, w3, w4, w5]:
            info_layout.addWidget(w)
        info_layout.addStretch()
        root.addLayout(info_layout)

        # ── 树形编辑器 ──
        self._tree = BomTreeWidget(self)
        self._tree.data_changed.connect(self._mark_dirty)
        root.addWidget(self._tree, stretch=1)

        # ── 底部状态 ──
        self._status_label = CaptionLabel("就绪")
        root.addWidget(self._status_label)

    def _load_items(self):
        if not self._proj:
            return
        items = bom_service.get_items(self._project_id)
        self._tree.load_items(items)
        self._dirty = False
        self._status_label.setText(f"已加载 {len(items)} 行明细")

    def _mark_dirty(self):
        if not self._dirty:
            self._dirty = True
            self._title_label.setText(
                f"BOM 编辑器 — {self._proj.bom_number} *"
            )

    # ── 保存 ───────────────────────────────────────────────────────

    def _on_save(self):
        if not self._proj:
            return
        items_data = self._tree.get_items()
        if not items_data:
            InfoBar.warning("提示", "BOM 明细为空，请先添加零件行",
                            parent=self, position=InfoBarPosition.TOP, duration=2500)
            return

        from app.ui.dialogs.change_reason_dialog import ChangeReasonDialog
        dlg = ChangeReasonDialog(self._proj.current_version, parent=self)
        if not dlg.exec():
            return

        change_data = dlg.get_data()
        try:
            bom_service.save_bom(
                project_id=self._project_id,
                items_data=items_data,
                new_version=change_data["new_version"],
                change_reason=change_data["change_reason"],
                change_description=change_data["change_description"],
                notes=change_data["notes"],
            )
            self._load_project()
            self._lbl_version.setText(self._proj.current_version)
            self._lbl_upd_date.setText(self._proj.updated_date or "")
            self._dirty = False
            self._title_label.setText(f"BOM 编辑器 — {self._proj.bom_number}")
            self._status_label.setText(f"已保存 {len(items_data)} 行  版本 → {change_data['new_version']}")
            InfoBar.success("保存成功", f"版本已更新为 {change_data['new_version']}",
                            parent=self, position=InfoBarPosition.TOP, duration=3000)
        except (ValueError, PermissionDenied) as e:
            InfoBar.error("保存失败", str(e), parent=self,
                          position=InfoBarPosition.TOP, duration=3000)

    # ── 导入 ───────────────────────────────────────────────────────

    def _on_import(self):
        from PySide6.QtWidgets import QFileDialog
        from app.utils.config_manager import ConfigManager
        from app.services.excel_service import import_bom_from_excel
        from app.ui.dialogs.import_preview_dialog import ImportPreviewDialog
        import os

        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Excel 文件", "",
            "Excel 文件 (*.xlsx *.xlsm *.xls)"
        )
        if not path:
            return

        try:
            result = import_bom_from_excel(path)
        except Exception as e:
            InfoBar.error("读取失败", str(e), parent=self,
                          position=InfoBarPosition.TOP, duration=3000)
            return

        require_confirm = ConfigManager().getbool("import", "require_preview_confirm", True)

        def _do_import(items, unknown_action):
            # 过滤陌生零件（根据用户选择）
            from app.services.part_service import get_part_by_number
            if unknown_action == "skip":
                items = [it for it in items
                         if get_part_by_number(it["part_number"])]
            self._tree.load_items(items)
            self._mark_dirty()
            InfoBar.success("导入成功",
                            f"已加载 {len(items)} 行明细，请检查后保存",
                            parent=self, position=InfoBarPosition.TOP, duration=3000)

        if require_confirm:
            dlg = ImportPreviewDialog(result, on_confirm=_do_import, parent=self)
            dlg.exec()
        else:
            if result.get("errors"):
                InfoBar.error("导入失败", "\n".join(result["errors"]),
                              parent=self, position=InfoBarPosition.TOP, duration=4000)
                return
            _do_import(result.get("items", []), "keep")

    # ── 导出 ───────────────────────────────────────────────────────

    def _on_export(self):
        from PySide6.QtWidgets import QFileDialog
        from app.utils.config_manager import ConfigManager
        import os
        default_dir = ConfigManager().get("export", "default_export_dir", "exports/")
        os.makedirs(default_dir, exist_ok=True)
        p = self._proj
        default_name = f"{p.bom_number}_{p.current_version}.xlsx" if p else "bom.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 BOM", f"{default_dir}{default_name}", "Excel 文件 (*.xlsx)"
        )
        if path:
            try:
                from app.services.excel_service import export_bom_to_excel
                export_bom_to_excel(self._project_id, path)
                InfoBar.success("导出成功", f"已保存至 {path}",
                                parent=self, position=InfoBarPosition.TOP, duration=3000)
            except Exception as e:
                InfoBar.error("导出失败", str(e), parent=self,
                              position=InfoBarPosition.TOP, duration=3000)

    # ── 历史版本 ───────────────────────────────────────────────────

    def _on_history(self):
        from app.ui.pages.bom_history_page import BomHistoryPage
        main_win = self.window()
        key = f"history_{self._project_id}"
        if not hasattr(main_win, "_editor_pages"):
            main_win._editor_pages = {}
        if key not in main_win._editor_pages:
            page = BomHistoryPage(self._project_id, main_win)
            main_win._editor_pages[key] = page
            main_win.addSubInterface(
                page, FluentIcon.HISTORY,
                f"历史: {self._proj.bom_number}" if self._proj else "变更历史",
            )
        main_win.switchTo(main_win._editor_pages[key])
