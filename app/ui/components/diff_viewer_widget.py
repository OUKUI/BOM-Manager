"""
BOM 版本差异对比控件
对比两个版本快照，行级高亮：
  绿色  — 新增行
  红色  — 删除行
  黄色  — 修改行（零件号相同但用量/备注变化）
  白色  — 无变化行
"""
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from qfluentwidgets import CaptionLabel, TableWidget

# diff 颜色
_COLOR_ADD    = QColor("#C8E6C9")   # 绿
_COLOR_DEL    = QColor("#FFCDD2")   # 红
_COLOR_MOD    = QColor("#FFF9C4")   # 黄
_COLOR_SAME   = QColor(0, 0, 0, 0)  # 透明（无变化）

_COLS = ["层级", "零件图号", "零件名称", "规格/材料", "单位", "用量", "备注"]


def _parse_items(snapshot_json: str) -> list[dict]:
    if not snapshot_json:
        return []
    try:
        raw = json.loads(snapshot_json)
    except Exception:
        return []
    result = []
    for d in raw:
        snap = {}
        if d.get("part_snapshot"):
            try:
                snap = json.loads(d["part_snapshot"]) if isinstance(d["part_snapshot"], str) else d["part_snapshot"]
            except Exception:
                pass
        result.append({
            "level":       d.get("level", 1),
            "part_number": d.get("part_number", ""),
            "name":        snap.get("name", ""),
            "spec":        snap.get("spec_material", ""),
            "unit":        snap.get("unit", ""),
            "quantity":    str(d.get("quantity", "")),
            "notes":       d.get("notes", ""),
        })
    return result


def _diff(old_items: list[dict], new_items: list[dict]) -> list[tuple]:
    """
    简单 LCS-based diff，返回 [(status, item_dict), ...]
    status: 'same' | 'add' | 'del' | 'mod'
    """
    old_map = {d["part_number"]: d for d in old_items}
    new_map = {d["part_number"]: d for d in new_items}

    result = []
    # 按新版本顺序展示
    for d in new_items:
        pn = d["part_number"]
        if pn not in old_map:
            result.append(("add", d))
        else:
            old = old_map[pn]
            if old["quantity"] != d["quantity"] or old["notes"] != d["notes"] or old["spec"] != d["spec"]:
                result.append(("mod", d))
            else:
                result.append(("same", d))

    # 已删除的行（在旧版本有、新版本无）
    for d in old_items:
        if d["part_number"] not in new_map:
            result.append(("del", d))

    return result


class DiffViewerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        legend = QHBoxLayout()
        for color, label in [
            (_COLOR_ADD, "新增"), (_COLOR_DEL, "删除"),
            (_COLOR_MOD, "修改"), (QColor("#E0E0E0"), "无变化"),
        ]:
            dot = QWidget()
            dot.setFixedSize(14, 14)
            dot.setStyleSheet(f"background:{color.name()};border-radius:3px;")
            legend.addWidget(dot)
            legend.addWidget(CaptionLabel(label))
            legend.addSpacing(12)
        legend.addStretch()
        layout.addLayout(legend)

        self._table = TableWidget(self)
        self._table.setColumnCount(len(_COLS))
        self._table.setHorizontalHeaderLabels(_COLS)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.Fixed); self._table.setColumnWidth(0, 44)
        hh.setSectionResizeMode(4, QHeaderView.Fixed); self._table.setColumnWidth(4, 52)
        hh.setSectionResizeMode(5, QHeaderView.Fixed); self._table.setColumnWidth(5, 60)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

    def compare(self, old_snapshot_json: str, new_snapshot_json: str):
        old_items = _parse_items(old_snapshot_json)
        new_items = _parse_items(new_snapshot_json)
        diff = _diff(old_items, new_items)

        self._table.setRowCount(0)
        color_map = {
            "add":  _COLOR_ADD,
            "del":  _COLOR_DEL,
            "mod":  _COLOR_MOD,
            "same": None,
        }
        for status, d in diff:
            row = self._table.rowCount()
            self._table.insertRow(row)
            bg = color_map.get(status)
            for col, val in enumerate([
                str(d["level"]), d["part_number"], d["name"],
                d["spec"], d["unit"], d["quantity"], d["notes"],
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if bg:
                    item.setBackground(bg)
                self._table.setItem(row, col, item)
