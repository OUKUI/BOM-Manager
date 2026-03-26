"""
BOM 管理系统 — 程序入口
"""
import sys
import os

# 确保运行目录为项目根目录（打包后也有效）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.utils.config_manager import ConfigManager
from app.utils.db import init_db
from app.ui.login_window import LoginWindow


def main():
    # 高 DPI 适配
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("BOM管理系统")

    # 初始化配置
    cfg = ConfigManager()

    # 初始化数据库（首次运行建表+创建默认超管）
    init_db()

    # 应用主题
    from qfluentwidgets import Theme, setTheme
    theme_str = cfg.get("app", "theme", "light")
    setTheme(Theme.DARK if theme_str == "dark" else Theme.LIGHT)

    # 显示登录窗口
    login = LoginWindow()
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
