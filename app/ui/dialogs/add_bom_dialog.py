"""
新建 BOM 项目对话框
"""
from PySide6.QtWidgets import QFormLayout
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, LineEdit,
    InfoBar, InfoBarPosition,
)


class AddBomDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("新建 BOM 项目", self)

        form = QFormLayout()
        form.setSpacing(10)

        self.f_bom_number = LineEdit(self)
        self.f_bom_number.setPlaceholderText("如 ED-72005-01")

        self.f_customer_pn = LineEdit(self)
        self.f_customer_pn.setPlaceholderText("客户零件号（可选）")

        self.f_customer_desc = LineEdit(self)
        self.f_customer_desc.setPlaceholderText("客户描述（可选）")

        self.f_project_name = LineEdit(self)
        self.f_project_name.setPlaceholderText("内部项目名称（可选）")

        self.f_version = LineEdit(self)
        self.f_version.setPlaceholderText("如 A01")
        self.f_version.setText("A01")
        self.f_version.setMaxLength(8)

        form.addRow("BOM 编号 *", self.f_bom_number)
        form.addRow("客户零件号", self.f_customer_pn)
        form.addRow("客户描述", self.f_customer_desc)
        form.addRow("项目名称", self.f_project_name)
        form.addRow("初始版本 *", self.f_version)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(8)
        self.viewLayout.addLayout(form)

        self.yesButton.setText("创建")
        self.cancelButton.setText("取消")

    def validate(self) -> bool:
        if not self.f_bom_number.text().strip():
            InfoBar.error("错误", "BOM 编号不能为空",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2000)
            return False
        if not self.f_version.text().strip():
            InfoBar.error("错误", "初始版本不能为空",
                          parent=self.window(), position=InfoBarPosition.TOP, duration=2000)
            return False
        return True

    def get_data(self) -> dict:
        return {
            "bom_number": self.f_bom_number.text().strip(),
            "customer_part_number": self.f_customer_pn.text().strip(),
            "customer_description": self.f_customer_desc.text().strip(),
            "project_name": self.f_project_name.text().strip(),
            "initial_version": self.f_version.text().strip(),
        }
