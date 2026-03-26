"""
保存 BOM 时填写变更原因对话框
"""
from PySide6.QtWidgets import QFormLayout
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, LineEdit, TextEdit,
    InfoBar, InfoBarPosition,
)


class ChangeReasonDialog(MessageBoxBase):
    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self._current_version = current_version

        self.titleLabel = SubtitleLabel("填写变更信息", self)

        form = QFormLayout()
        form.setSpacing(10)

        self.f_new_version = LineEdit(self)
        self.f_new_version.setPlaceholderText("如 A02")
        self.f_new_version.setMaxLength(8)

        self.f_reason = LineEdit(self)
        self.f_reason.setPlaceholderText("变更原因（必填）")

        self.f_description = TextEdit(self)
        self.f_description.setPlaceholderText("变更内容描述（可选）")
        self.f_description.setFixedHeight(80)

        self.f_notes = LineEdit(self)
        self.f_notes.setPlaceholderText("备注（可选）")

        form.addRow("新版本号 *", self.f_new_version)
        form.addRow("变更原因 *", self.f_reason)
        form.addRow("变更内容", self.f_description)
        form.addRow("备注", self.f_notes)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addLayout(form)

        self.yesButton.setText("确认保存")
        self.cancelButton.setText("取消")

    def validate(self) -> bool:
        if not self.f_new_version.text().strip():
            InfoBar.error("错误", "新版本号不能为空",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2000)
            return False
        if not self.f_reason.text().strip():
            InfoBar.error("错误", "变更原因不能为空",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2000)
            return False
        return True

    def get_data(self) -> dict:
        return {
            "new_version": self.f_new_version.text().strip(),
            "change_reason": self.f_reason.text().strip(),
            "change_description": self.f_description.toPlainText().strip(),
            "notes": self.f_notes.text().strip(),
        }
