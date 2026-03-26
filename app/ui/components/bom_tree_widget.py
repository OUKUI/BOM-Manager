"""
BOM 树形表格组件
- 支持层级缩进显示（level 决定缩进量）
- 层级标记列（*, ■, 空）
- 上移/下移/升级/降级
- 新增行 / 删除行
- 零件图号输入后自动从母表填充名称/规格等（快照信息）
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSpinBox, QDoubleSpinBox, QComboBox,
    QLineEdit,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QKeyEvent
from PySide6.QtWidgets import QApplication
from qfluentwidgets import (
    PushButton, ToolButton, FluentIcon, ComboBox,
)

_COLS = ["标记", "层级", "序号", "零件图号", "零件版本", "零件标准", "零件名称", "规格/材料", "单位", "用量", "备注"]
_COL_MARK      = 0
_COL_LEVEL     = 1
_COL_SEQ       = 2
_COL_PARTNO    = 3
_COL_VER       = 4
_COL_STD       = 5
_COL_NAME      = 6
_COL_SPEC      = 7
_COL_UNIT      = 8
_COL_QTY       = 9
_COL_NOTES     = 10

_MARK_OPTIONS = ["", "*", "■", "▲", "●"]
_LEVEL_LABELS = ["", "一", "二", "三", "四", "五"]


class BomTreeWidget(QWidget):
    """可编辑的 BOM 树形表格组件"""
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 工具栏
        bar = QHBoxLayout()
        bar.setSpacing(6)

        def _btn(icon, tip, slot):
            b = ToolButton(icon, self)
            b.setToolTip(tip)
            b.setFixedSize(32, 32)
            b.clicked.connect(slot)
            bar.addWidget(b)
            return b

        _btn(FluentIcon.ADD, "新增行（在选中行下方）", self._add_row)
        _btn(FluentIcon.REMOVE, "删除选中行", self._delete_row)
        bar.addSpacing(8)
        _btn(FluentIcon.UP, "上移", self._move_up)
        _btn(FluentIcon.DOWN, "下移", self._move_down)
        bar.addSpacing(8)
        _btn(FluentIcon.RETURN, "降级（增加层级）", self._indent)
        _btn(FluentIcon.BACK_TO_WINDOW, "升级（减少层级）", self._unindent)
        bar.addStretch()

        layout.addLayout(bar)

        # 表格
        self._table = QTableWidget(self)
        self._table.setColumnCount(len(_COLS))
        self._table.setHorizontalHeaderLabels(_COLS)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(_COL_MARK,  QHeaderView.Fixed);  self._table.setColumnWidth(_COL_MARK, 48)
        hh.setSectionResizeMode(_COL_LEVEL, QHeaderView.Fixed);  self._table.setColumnWidth(_COL_LEVEL, 44)
        hh.setSectionResizeMode(_COL_SEQ,   QHeaderView.Fixed);  self._table.setColumnWidth(_COL_SEQ, 60)
        hh.setSectionResizeMode(_COL_PARTNO,QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(_COL_VER,   QHeaderView.Fixed);  self._table.setColumnWidth(_COL_VER, 60)
        hh.setSectionResizeMode(_COL_STD,   QHeaderView.Fixed);  self._table.setColumnWidth(_COL_STD, 60)
        hh.setSectionResizeMode(_COL_UNIT,  QHeaderView.Fixed);  self._table.setColumnWidth(_COL_UNIT, 52)
        hh.setSectionResizeMode(_COL_QTY,   QHeaderView.Fixed);  self._table.setColumnWidth(_COL_QTY, 60)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self._table)

    # ── 键盘事件：Ctrl+V 粘贴 ──────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent):
        if event.matches(QKeySequence.Paste):
            self._paste_from_clipboard()
        else:
            super().keyPressEvent(event)

    def _paste_from_clipboard(self):
        """
        粘贴 Excel 复制内容（Tab 分隔列，\\n 分隔行）。
        列映射（从左到右）：
          零件图号 | 零件版本 | 零件名称 | 规格/材料 | 单位 | 用量 | 备注
        可以只粘贴部分列（从第1列"零件图号"开始）。
        粘贴插入位置：选中行之后；若未选中则追加到末尾。
        """
        text = QApplication.clipboard().text()
        if not text.strip():
            return

        rows_raw = text.rstrip("\n").split("\n")
        insert_at = self._table.currentRow() + 1
        if insert_at <= 0:
            insert_at = self._table.rowCount()

        self._table.blockSignals(True)
        pasted_count = 0
        for raw_row in rows_raw:
            cols_data = raw_row.split("\t")
            if not cols_data or not cols_data[0].strip():
                continue
            self._table.insertRow(insert_at + pasted_count)
            self._init_row(insert_at + pasted_count, level=1)

            mapping = [
                (_COL_PARTNO, 0),
                (_COL_VER,    1),
                (_COL_NAME,   2),
                (_COL_SPEC,   3),
                (_COL_UNIT,   4),
                (_COL_QTY,    5),
                (_COL_NOTES,  6),
            ]
            for table_col, paste_col in mapping:
                if paste_col < len(cols_data):
                    val = cols_data[paste_col].strip()
                    if table_col == _COL_QTY:
                        try:
                            qty = float(val) if val else 1.0
                        except ValueError:
                            qty = 1.0
                        item = QTableWidgetItem(str(qty))
                        item.setTextAlignment(Qt.AlignCenter)
                        self._table.setItem(insert_at + pasted_count, table_col, item)
                    elif table_col in (_COL_VER, _COL_STD, _COL_NAME, _COL_SPEC, _COL_UNIT):
                        # 这些列在 _set_cell 中是只读的，直接设置 item
                        item = QTableWidgetItem(val)
                        self._table.setItem(insert_at + pasted_count, table_col, item)
                    else:
                        self._set_cell(insert_at + pasted_count, table_col, val)
            pasted_count += 1

        self._refresh_seq()
        self._table.blockSignals(False)

        if pasted_count > 0:
            self.data_changed.emit()

    # ── 数据接口 ───────────────────────────────────────────────────

    def load_items(self, items: list):
        """items: BomItem 列表 或 dict 列表"""
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        for item in items:
            if hasattr(item, "part_number"):
                d = {
                    "level": item.level,
                    "level_mark": item.level_mark or "",
                    "level_label": item.level_label or "",
                    "part_number": item.part_number,
                    "quantity": item.quantity,
                    "notes": item.notes or "",
                    "part_snapshot": item.part_snapshot,
                }
            else:
                d = item
            self._append_row_from_dict(d)
        self._refresh_seq()
        self._table.blockSignals(False)

    def get_items(self) -> list[dict]:
        """返回当前表格数据，供 bom_service.save_bom 使用"""
        result = []
        for row in range(self._table.rowCount()):
            part_no = self._get_cell(row, _COL_PARTNO)
            if not part_no:
                continue
            result.append({
                "sort_order": row,
                "level": int(self._get_cell(row, _COL_LEVEL) or 1),
                "level_mark": self._get_cell(row, _COL_MARK),
                "level_label": _LEVEL_LABELS[min(int(self._get_cell(row, _COL_LEVEL) or 1),
                                                  len(_LEVEL_LABELS) - 1)],
                "part_number": part_no,
                "quantity": self._get_qty(row),
                "notes": self._get_cell(row, _COL_NOTES),
            })
        return result

    # ── 行操作 ─────────────────────────────────────────────────────

    def _add_row(self):
        sel = self._table.currentRow()
        insert_at = sel + 1 if sel >= 0 else self._table.rowCount()
        level = int(self._get_cell(sel, _COL_LEVEL) or 1) if sel >= 0 else 1
        self._table.blockSignals(True)
        self._table.insertRow(insert_at)
        self._init_row(insert_at, level=level)
        self._refresh_seq()
        self._table.blockSignals(False)
        self._table.selectRow(insert_at)
        self.data_changed.emit()

    def _delete_row(self):
        sel = self._table.currentRow()
        if sel < 0:
            return
        self._table.removeRow(sel)
        self._refresh_seq()
        self.data_changed.emit()

    def _move_up(self):
        sel = self._table.currentRow()
        if sel <= 0:
            return
        self._swap_rows(sel, sel - 1)
        self._table.selectRow(sel - 1)
        self._refresh_seq()
        self.data_changed.emit()

    def _move_down(self):
        sel = self._table.currentRow()
        if sel < 0 or sel >= self._table.rowCount() - 1:
            return
        self._swap_rows(sel, sel + 1)
        self._table.selectRow(sel + 1)
        self._refresh_seq()
        self.data_changed.emit()

    def _indent(self):
        sel = self._table.currentRow()
        if sel < 0:
            return
        level = int(self._get_cell(sel, _COL_LEVEL) or 1)
        self._set_cell(sel, _COL_LEVEL, str(min(level + 1, 5)))
        self._refresh_level_display(sel)
        self.data_changed.emit()

    def _unindent(self):
        sel = self._table.currentRow()
        if sel < 0:
            return
        level = int(self._get_cell(sel, _COL_LEVEL) or 1)
        self._set_cell(sel, _COL_LEVEL, str(max(level - 1, 1)))
        self._refresh_level_display(sel)
        self.data_changed.emit()

    # ── 零件图号变更时自动填充 ─────────────────────────────────────

    def _on_item_changed(self, item: QTableWidgetItem):
        if item.column() == _COL_PARTNO:
            self._auto_fill_part(item.row(), item.text().strip())
            self.data_changed.emit()

    def _auto_fill_part(self, row: int, part_number: str):
        if not part_number:
            return
        from app.services.part_service import get_part_by_number
        part = get_part_by_number(part_number)
        if part:
            self._table.blockSignals(True)
            self._set_cell(row, _COL_VER,  part.version or "")
            self._set_cell(row, _COL_STD,  part.standard_level or "")
            self._set_cell(row, _COL_NAME, part.name or "")
            self._set_cell(row, _COL_SPEC, part.spec_material or "")
            self._set_cell(row, _COL_UNIT, part.unit or "")
            self._table.blockSignals(False)

    # ── 辅助方法 ───────────────────────────────────────────────────

    def _init_row(self, row: int, level: int = 1):
        self._set_cell(row, _COL_MARK,  "")
        self._set_cell(row, _COL_LEVEL, str(level))
        self._set_cell(row, _COL_SEQ,   "")
        for col in [_COL_PARTNO, _COL_VER, _COL_STD, _COL_NAME, _COL_SPEC, _COL_UNIT, _COL_NOTES]:
            self._set_cell(row, col, "")
        qty_item = QTableWidgetItem("1")
        qty_item.setTextAlignment(Qt.AlignCenter)
        self._table.setItem(row, _COL_QTY, qty_item)

    def _append_row_from_dict(self, d: dict):
        import json
        row = self._table.rowCount()
        self._table.insertRow(row)
        level = d.get("level", 1)
        snap = d.get("part_snapshot")
        snap_dict = {}
        if snap:
            try:
                snap_dict = json.loads(snap) if isinstance(snap, str) else snap
            except Exception:
                pass

        self._set_cell(row, _COL_MARK,  d.get("level_mark", ""))
        self._set_cell(row, _COL_LEVEL, str(level))
        self._set_cell(row, _COL_PARTNO,d.get("part_number", ""))
        self._set_cell(row, _COL_VER,   snap_dict.get("version", ""))
        self._set_cell(row, _COL_STD,   snap_dict.get("standard_level", ""))
        self._set_cell(row, _COL_NAME,  snap_dict.get("name", ""))
        self._set_cell(row, _COL_SPEC,  snap_dict.get("spec_material", ""))
        self._set_cell(row, _COL_UNIT,  snap_dict.get("unit", ""))
        qty_item = QTableWidgetItem(str(d.get("quantity", 1)))
        qty_item.setTextAlignment(Qt.AlignCenter)
        self._table.setItem(row, _COL_QTY, qty_item)
        self._set_cell(row, _COL_NOTES, d.get("notes", ""))
        self._refresh_level_display(row)

    def _refresh_seq(self):
        """根据 level 重新生成序号（1 / 1.1 / 1.1.1 风格）"""
        counters = [0] * 6
        for row in range(self._table.rowCount()):
            level = int(self._get_cell(row, _COL_LEVEL) or 1)
            level = max(1, min(level, 5))
            counters[level] += 1
            for i in range(level + 1, 6):
                counters[i] = 0
            seq = ".".join(str(counters[i]) for i in range(1, level + 1))
            item = QTableWidgetItem(seq)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self._table.setItem(row, _COL_SEQ, item)

    def _refresh_level_display(self, row: int):
        level = int(self._get_cell(row, _COL_LEVEL) or 1)
        # 缩进效果：在名称列前添加空格
        name_item = self._table.item(row, _COL_NAME)
        if name_item:
            text = name_item.text().lstrip()
            name_item.setText("  " * (level - 1) + text)

    def _swap_rows(self, row_a: int, row_b: int):
        for col in range(self._table.columnCount()):
            item_a = self._table.takeItem(row_a, col)
            item_b = self._table.takeItem(row_b, col)
            self._table.setItem(row_a, col, item_b)
            self._table.setItem(row_b, col, item_a)

    def _get_cell(self, row: int, col: int) -> str:
        item = self._table.item(row, col)
        return item.text() if item else ""

    def _set_cell(self, row: int, col: int, value: str):
        item = QTableWidgetItem(value)
        if col in (_COL_SEQ, _COL_VER, _COL_STD, _COL_NAME, _COL_SPEC, _COL_UNIT):
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self._table.setItem(row, col, item)

    def _get_qty(self, row: int) -> float:
        try:
            return float(self._get_cell(row, _COL_QTY))
        except ValueError:
            return 1.0
