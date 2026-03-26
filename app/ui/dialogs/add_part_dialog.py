"""
新增/编辑零件对话框
"""
from PySide6.QtWidgets import QFormLayout, QDoubleSpinBox
from PySide6.QtCore import Qt
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, LineEdit, ComboBox,
    InfoBar, InfoBarPosition, TextEdit,
)
from app.models import PartsMaster


class AddPartDialog(MessageBoxBase):
    def __init__(self, part: PartsMaster = None, parent=None):
        super().__init__(parent)
        self._part = part
        is_edit = part is not None

        self.titleLabel = SubtitleLabel("编辑零件" if is_edit else "新增零件", self)

        form = QFormLayout()
        form.setSpacing(10)

        self.f_number = LineEdit(self)
        self.f_number.setPlaceholderText("如 ED-15302-01")
        if is_edit:
            self.f_number.setText(part.part_number)
            self.f_number.setReadOnly(True)

        self.f_version = LineEdit(self)
        self.f_version.setPlaceholderText("如 A03")
        self.f_version.setMaxLength(8)

        self.f_standard = ComboBox(self)
        self.f_standard.addItems(["", "主要", "要", "次要"])

        self.f_name = LineEdit(self)
        self.f_name.setPlaceholderText("零件名称")

        self.f_spec = TextEdit(self)
        self.f_spec.setPlaceholderText("规格/材料（可多行）")
        self.f_spec.setFixedHeight(72)

        self.f_unit = LineEdit(self)
        self.f_unit.setPlaceholderText("pcs")
        self.f_unit.setMaxLength(8)

        self.f_qty = QDoubleSpinBox(self)
        self.f_qty.setRange(0.01, 99999)
        self.f_qty.setValue(1.0)
        self.f_qty.setDecimals(2)

        self.f_notes = LineEdit(self)
        self.f_notes.setPlaceholderText("备注")

        form.addRow("零件图号 *", self.f_number)
        form.addRow("零件版本 *", self.f_version)
        form.addRow("零件标准", self.f_standard)
        form.addRow("零件名称 *", self.f_name)
        form.addRow("规格/材料", self.f_spec)
        form.addRow("单位", self.f_unit)
        form.addRow("默认用量", self.f_qty)
        form.addRow("备注", self.f_notes)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addLayout(form)

        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

        if is_edit:
            self.f_version.setText(part.version or "")
            idx = self.f_standard.findText(part.standard_level or "")
            self.f_standard.setCurrentIndex(max(0, idx))
            self.f_name.setText(part.name or "")
            self.f_spec.setPlainText(part.spec_material or "")
            self.f_unit.setText(part.unit or "")
            self.f_qty.setValue(part.default_qty or 1.0)
            self.f_notes.setText(part.notes or "")

    def validate(self) -> bool:
        if not self.f_number.text().strip():
            InfoBar.error("错误", "零件图号不能为空",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2000)
            return False
        if not self.f_version.text().strip():
            InfoBar.error("错误", "零件版本不能为空",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2000)
            return False
        if not self.f_name.text().strip():
            InfoBar.error("错误", "零件名称不能为空",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2000)
            return False
        return True

    def get_data(self) -> dict:
        return {
            "part_number": self.f_number.text().strip(),
            "version": self.f_version.text().strip(),
            "standard_level": self.f_standard.currentText() or None,
            "name": self.f_name.text().strip(),
            "spec_material": self.f_spec.toPlainText().strip() or None,
            "unit": self.f_unit.text().strip() or "pcs",
            "default_qty": self.f_qty.value(),
            "notes": self.f_notes.text().strip() or None,
        }
