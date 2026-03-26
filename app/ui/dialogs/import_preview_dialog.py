"""
Excel 导入预检报告弹窗
- 展示预检结果：错误（红）、警告（黄）、正常行数
- 陌生零件处理策略选择
- 确认后回调写入数据库
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, CaptionLabel,
    TableWidget, ComboBox, InfoBar, InfoBarPosition,
)


class ImportPreviewDialog(MessageBoxBase):
    """
    preview_result: dict from excel_service.import_bom_from_excel()
    on_confirm(items, unknown_action): callable，用户确认后回调
    """
    def __init__(self, preview_result: dict, on_confirm=None, parent=None):
        super().__init__(parent)
        self._result = preview_result
        self._on_confirm = on_confirm

        self.titleLabel = SubtitleLabel("导入预检报告", self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(8)

        errors = preview_result.get("errors", [])
        warnings = preview_result.get("warnings", [])
        items = preview_result.get("items", [])

        summary_row = QHBoxLayout()
        summary_row.setSpacing(24)
        summary_row.addWidget(self._stat_card("BOM 编号",   preview_result.get("bom_number", "—")))
        summary_row.addWidget(self._stat_card("版本",       preview_result.get("version", "—")))
        summary_row.addWidget(self._stat_card("明细行数",   str(len(items))))
        summary_row.addWidget(self._stat_card("错误",       str(len(errors)), "#E74C3C" if errors else None))
        summary_row.addWidget(self._stat_card("警告",       str(len(warnings)), "#F39C12" if warnings else None))
        summary_row.addStretch()
        self.viewLayout.addLayout(summary_row)
        self.viewLayout.addSpacing(8)

        if errors or warnings:
            self.viewLayout.addWidget(CaptionLabel("问题详情："))
            issue_table = TableWidget(self)
            issue_table.setColumnCount(2)
            issue_table.setHorizontalHeaderLabels(["级别", "说明"])
            issue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            issue_table.setColumnWidth(0, 60)
            issue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            issue_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            issue_table.verticalHeader().setVisible(False)
            issue_table.setFixedHeight(min(200, (len(errors) + len(warnings) + 1) * 30))

            for msg in errors:
                r = issue_table.rowCount()
                issue_table.insertRow(r)
                lv = QTableWidgetItem("❌ 错误")
                lv.setForeground(QColor("#E74C3C"))
                issue_table.setItem(r, 0, lv)
                issue_table.setItem(r, 1, QTableWidgetItem(msg))

            for msg in warnings:
                r = issue_table.rowCount()
                issue_table.insertRow(r)
                lv = QTableWidgetItem("⚠️ 警告")
                lv.setForeground(QColor("#F39C12"))
                issue_table.setItem(r, 0, lv)
                issue_table.setItem(r, 1, QTableWidgetItem(msg))

            self.viewLayout.addWidget(issue_table)
            self.viewLayout.addSpacing(8)

        if warnings:
            strategy_row = QHBoxLayout()
            strategy_row.addWidget(CaptionLabel("陌生零件处理："))
            self._unknown_action = ComboBox(self)
            self._unknown_action.addItems(["跳过该行", "仍然导入（零件图号保留，母表信息留空）"])
            strategy_row.addWidget(self._unknown_action)
            strategy_row.addStretch()
            self.viewLayout.addLayout(strategy_row)
        else:
            self._unknown_action = None

        self.yesButton.setText("确认导入" if not errors else "关闭")
        self.cancelButton.setText("取消")
        if errors:
            self.cancelButton.hide()

    def _stat_card(self, label: str, value: str, color: str = None) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 8, 12, 8)
        l.setSpacing(2)
        lbl = CaptionLabel(label)
        val = SubtitleLabel(value)
        if color:
            val.setStyleSheet(f"color: {color}; font-weight: bold;")
        l.addWidget(lbl)
        l.addWidget(val)
        w.setStyleSheet("QWidget { border: 1px solid rgba(128,128,128,60); border-radius: 6px; }")
        return w

    def validate(self) -> bool:
        errors = self._result.get("errors", [])
        if errors:
            return True  # 只是关闭对话框
        action = "skip"
        if self._unknown_action and self._unknown_action.currentIndex() == 1:
            action = "keep"
        if self._on_confirm:
            self._on_confirm(self._result.get("items", []), action)
        return True
