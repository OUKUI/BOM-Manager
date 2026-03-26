"""
配置管理单例，封装 configparser，变更立即写入 config.ini
"""
import os
import configparser
from typing import Optional

_DEFAULT_CONFIG = {
    "app": {
        "theme": "light",
        "language": "zh_CN",
        "font_size": "14",
        "window_maximized": "false",
        "window_width": "1280",
        "window_height": "800",
    },
    "database": {
        "path": "data/bom.db",
        "auto_backup": "false",
        "backup_keep_count": "7",
    },
    "security": {
        "min_password_length": "8",
        "pwd_require_upper": "true",
        "pwd_require_digit": "true",
        "pwd_require_special": "false",
        "session_timeout_minutes": "0",
        "lockout_enabled": "false",
    },
    "export": {
        "default_export_dir": "exports/",
        "include_change_log": "true",
        "use_snapshot": "true",
        "filename_pattern": "bom_version",
    },
    "import": {
        "unknown_part_action": "prompt",
        "require_preview_confirm": "true",
    },
}

CONFIG_PATH = "config.ini"


class ConfigManager:
    _instance: Optional["ConfigManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._parser = configparser.ConfigParser()
        # 设置默认值
        for section, values in _DEFAULT_CONFIG.items():
            if not self._parser.has_section(section):
                self._parser.add_section(section)
            for key, val in values.items():
                self._parser.set(section, key, val)
        # 读取已有配置（覆盖默认）
        if os.path.exists(CONFIG_PATH):
            self._parser.read(CONFIG_PATH, encoding="utf-8")
        else:
            self._save()

    def _save(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            self._parser.write(f)

    def get(self, section: str, key: str, fallback: str = "") -> str:
        return self._parser.get(section, key, fallback=fallback)

    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        return self._parser.getint(section, key, fallback=fallback)

    def getbool(self, section: str, key: str, fallback: bool = False) -> bool:
        return self._parser.getboolean(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str):
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        self._parser.set(section, key, str(value))
        self._save()
