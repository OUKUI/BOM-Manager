"""
系统设置页面 — 5个分组，使用 QFluentWidgets SettingCardGroup
"""
import os
import shutil
from datetime import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import (
    ScrollArea, TitleLabel, SettingCardGroup, SettingCard,
    SwitchSettingCard, ComboBoxSettingCard, PushSettingCard,
    FluentIcon as FI, InfoBar, InfoBarPosition, Theme, setTheme,
    OptionsConfigItem, OptionsValidator,
)
from app.utils.config_manager import ConfigManager
from app.core.auth import AuthContext
from version import VERSION, APP_NAME, BUILD_DATE


def _opt(group: str, name: str, default: str, options: list) -> OptionsConfigItem:
    """创建一个独立的 OptionsConfigItem，不绑定到 qconfig。"""
    return OptionsConfigItem(group, name, default, OptionsValidator(options))


class SettingsPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPage")
        self.setWidgetResizable(True)
        self._cfg = ConfigManager()
        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignTop)

        layout.addWidget(TitleLabel("系统设置"))
        layout.addWidget(self._group_appearance())
        layout.addWidget(self._group_data())
        layout.addWidget(self._group_security())
        layout.addWidget(self._group_import_export())
        layout.addWidget(self._group_about())

        self.setWidget(root)

    # ── 分组 1：外观与语言 ─────────────────────────────────────────

    def _group_appearance(self):
        group = SettingCardGroup("外观与语言", self)

        # 主题模式
        cur_theme = self._cfg.get("app", "theme", "light")
        theme_item = _opt("app", "theme", cur_theme, ["light", "dark", "auto"])
        self._theme_card = ComboBoxSettingCard(
            theme_item, FI.CONSTRACT, "主题模式",
            "切换浅色/深色界面风格",
            texts=["浅色", "深色", "跟随系统"],
            parent=group,
        )
        theme_item.valueChanged.connect(self._on_theme_changed)
        group.addSettingCard(self._theme_card)

        # 字体大小
        cur_font = self._cfg.get("app", "font_size", "14")
        font_item = _opt("app", "font_size", cur_font, ["12", "14", "16"])
        self._font_card = ComboBoxSettingCard(
            font_item, FI.FONT, "字体大小",
            "调整界面字体大小",
            texts=["小 (12px)", "中 (14px)", "大 (16px)"],
            parent=group,
        )
        font_item.valueChanged.connect(
            lambda v: self._cfg.set("app", "font_size", v)
        )
        group.addSettingCard(self._font_card)

        # 启动时最大化
        self._maximize_card = SwitchSettingCard(
            FI.FULL_SCREEN, "启动时最大化",
            "程序启动后自动最大化窗口",
            parent=group,
        )
        self._maximize_card.switchButton.setChecked(
            self._cfg.getbool("app", "window_maximized", False)
        )
        self._maximize_card.switchButton.checkedChanged.connect(
            lambda v: self._cfg.set("app", "window_maximized", "true" if v else "false")
        )
        group.addSettingCard(self._maximize_card)

        return group

    def _on_theme_changed(self, v: str):
        self._cfg.set("app", "theme", v)
        setTheme({"light": Theme.LIGHT, "dark": Theme.DARK, "auto": Theme.AUTO}.get(v, Theme.LIGHT))

    # ── 分组 2：数据与存储 ─────────────────────────────────────────

    def _group_data(self):
        group = SettingCardGroup("数据与存储", self)

        db_path = os.path.abspath(self._cfg.get("database", "path", "data/bom.db"))
        self._db_path_card = PushSettingCard(
            "打开目录", FI.FOLDER, "数据库文件", db_path,
            parent=group,
        )
        self._db_path_card.clicked.connect(
            lambda: os.startfile(os.path.dirname(db_path))
        )
        group.addSettingCard(self._db_path_card)

        self._backup_now_card = PushSettingCard(
            "立即备份", FI.SAVE_COPY, "立即备份数据库",
            "将当前数据库复制为带时间戳的备份文件",
            parent=group,
        )
        self._backup_now_card.clicked.connect(self._do_backup)
        group.addSettingCard(self._backup_now_card)

        self._auto_backup_card = SwitchSettingCard(
            FI.SYNC, "启动时自动备份",
            "每次程序启动时自动备份，保留最近 N 份",
            parent=group,
        )
        self._auto_backup_card.switchButton.setChecked(
            self._cfg.getbool("database", "auto_backup", False)
        )
        self._auto_backup_card.switchButton.checkedChanged.connect(
            lambda v: self._cfg.set("database", "auto_backup", "true" if v else "false")
        )
        group.addSettingCard(self._auto_backup_card)

        export_dir = os.path.abspath(self._cfg.get("export", "default_export_dir", "exports/"))
        self._export_dir_card = PushSettingCard(
            "更改目录", FI.SHARE, "默认导出目录", export_dir,
            parent=group,
        )
        self._export_dir_card.clicked.connect(self._change_export_dir)
        group.addSettingCard(self._export_dir_card)

        return group

    def _do_backup(self):
        db_path = self._cfg.get("database", "path", "data/bom.db")
        if not os.path.exists(db_path):
            InfoBar.error("备份失败", "数据库文件不存在", parent=self,
                          position=InfoBarPosition.TOP, duration=3000)
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = f"{db_path[:-3]}_backup_{ts}.db"
        shutil.copy2(db_path, dest)
        from app.core.audit import write_audit
        write_audit("EXPORT", resource_type="DB", detail=f"数据库备份: {dest}")
        InfoBar.success("备份成功", f"已保存至 {os.path.basename(dest)}", parent=self,
                        position=InfoBarPosition.TOP, duration=3000)

    def _change_export_dir(self):
        from PySide6.QtWidgets import QFileDialog
        d = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if d:
            self._cfg.set("export", "default_export_dir", d + "/")
            self._export_dir_card.setContent(d)

    # ── 分组 3：安全与账户 ─────────────────────────────────────────

    def _group_security(self):
        group = SettingCardGroup("安全与账户", self)

        ctx = AuthContext()
        user_info = (
            f"{ctx.user.display_name}（{ctx.user.username}） | 角色: {ctx.role}"
            if ctx.user else "未登录"
        )
        self._login_info_card = PushSettingCard(
            "退出登录", FI.PEOPLE, "当前登录账户", user_info,
            parent=group,
        )
        self._login_info_card.clicked.connect(self._logout)
        group.addSettingCard(self._login_info_card)

        cur_timeout = str(self._cfg.getint("security", "session_timeout_minutes", 0))
        if cur_timeout not in ["0", "60", "240", "480"]:
            cur_timeout = "0"
        timeout_item = _opt("security", "session_timeout_minutes", cur_timeout,
                            ["0", "60", "240", "480"])
        self._timeout_card = ComboBoxSettingCard(
            timeout_item, FI.STOP_WATCH, "会话超时",
            "闲置超时后自动退出登录",
            texts=["不超时", "1 小时", "4 小时", "8 小时"],
            parent=group,
        )
        timeout_item.valueChanged.connect(
            lambda v: self._cfg.set("security", "session_timeout_minutes", v)
        )
        group.addSettingCard(self._timeout_card)

        self._lockout_card = SwitchSettingCard(
            FI.CANCEL, "登录失败锁定",
            "连续失败 5 次后锁定账户 15 分钟",
            parent=group,
        )
        self._lockout_card.switchButton.setChecked(
            self._cfg.getbool("security", "lockout_enabled", False)
        )
        self._lockout_card.switchButton.checkedChanged.connect(
            lambda v: self._cfg.set("security", "lockout_enabled", "true" if v else "false")
        )
        group.addSettingCard(self._lockout_card)

        return group

    def _logout(self):
        from qfluentwidgets import MessageBox
        box = MessageBox("退出登录", "确认退出当前账户并返回登录界面？", self)
        if box.exec():
            from app.core.audit import write_audit
            write_audit("LOGOUT")
            AuthContext().logout()
            from app.ui.login_window import LoginWindow
            win = self.window()
            self._login = LoginWindow()
            self._login.show()
            win.close()

    # ── 分组 4：导入与导出 ─────────────────────────────────────────

    def _group_import_export(self):
        group = SettingCardGroup("导入与导出", self)

        self._include_changelog_card = SwitchSettingCard(
            FI.HISTORY, "导出时包含变更履历",
            "在导出的 Excel 中附带变更履历 Sheet",
            parent=group,
        )
        self._include_changelog_card.switchButton.setChecked(
            self._cfg.getbool("export", "include_change_log", True)
        )
        self._include_changelog_card.switchButton.checkedChanged.connect(
            lambda v: self._cfg.set("export", "include_change_log", "true" if v else "false")
        )
        group.addSettingCard(self._include_changelog_card)

        self._use_snapshot_card = SwitchSettingCard(
            FI.TAG, "导出时使用零件快照",
            "以 BOM 保存时的数据导出，而非实时查询母表",
            parent=group,
        )
        self._use_snapshot_card.switchButton.setChecked(
            self._cfg.getbool("export", "use_snapshot", True)
        )
        self._use_snapshot_card.switchButton.checkedChanged.connect(
            lambda v: self._cfg.set("export", "use_snapshot", "true" if v else "false")
        )
        group.addSettingCard(self._use_snapshot_card)

        cur_fn = self._cfg.get("export", "filename_pattern", "bom_version")
        if cur_fn not in ["bom_version", "bom_date", "manual"]:
            cur_fn = "bom_version"
        fn_item = _opt("export", "filename_pattern", cur_fn,
                       ["bom_version", "bom_date", "manual"])
        self._filename_card = ComboBoxSettingCard(
            fn_item, FI.EDIT, "导出文件命名规则",
            "导出 Excel 时的文件名格式",
            texts=["BOM编号_版本", "BOM编号_日期", "手动命名"],
            parent=group,
        )
        fn_item.valueChanged.connect(
            lambda v: self._cfg.set("export", "filename_pattern", v)
        )
        group.addSettingCard(self._filename_card)

        cur_up = self._cfg.get("import", "unknown_part_action", "prompt")
        if cur_up not in ["error", "skip", "prompt"]:
            cur_up = "prompt"
        up_item = _opt("import", "unknown_part_action", cur_up,
                       ["error", "skip", "prompt"])
        self._unknown_part_card = ComboBoxSettingCard(
            up_item, FI.QUESTION, "导入时陌生零件处理",
            "遇到母表中不存在的零件图号时的处理策略",
            texts=["报错中止", "跳过该行", "提示后决定"],
            parent=group,
        )
        up_item.valueChanged.connect(
            lambda v: self._cfg.set("import", "unknown_part_action", v)
        )
        group.addSettingCard(self._unknown_part_card)

        self._preview_confirm_card = SwitchSettingCard(
            FI.ACCEPT, "导入前显示预检报告",
            "导入前展示格式/逻辑错误摘要，确认后再写入",
            parent=group,
        )
        self._preview_confirm_card.switchButton.setChecked(
            self._cfg.getbool("import", "require_preview_confirm", True)
        )
        self._preview_confirm_card.switchButton.checkedChanged.connect(
            lambda v: self._cfg.set("import", "require_preview_confirm", "true" if v else "false")
        )
        group.addSettingCard(self._preview_confirm_card)

        return group

    # ── 分组 5：关于 ───────────────────────────────────────────────

    def _group_about(self):
        group = SettingCardGroup("关于", self)

        # 版本信息（无按钮，用 SettingCard）
        group.addSettingCard(SettingCard(
            FI.INFO, APP_NAME,
            f"版本 {VERSION}  |  构建日期 {BUILD_DATE}",
            parent=group,
        ))

        self._log_card = PushSettingCard(
            "打开", FI.FOLDER, "查看日志文件夹",
            os.path.abspath("logs/"),
            parent=group,
        )
        self._log_card.clicked.connect(
            lambda: os.makedirs("logs", exist_ok=True) or os.startfile(os.path.abspath("logs"))
        )
        group.addSettingCard(self._log_card)

        self._reset_card = PushSettingCard(
            "重置", FI.DELETE, "重置所有设置",
            "将 config.ini 恢复为默认值，重启后生效",
            parent=group,
        )
        self._reset_card.clicked.connect(self._reset_settings)
        group.addSettingCard(self._reset_card)

        return group

    def _reset_settings(self):
        from qfluentwidgets import MessageBox
        box = MessageBox(
            "确认重置",
            "将清除所有自定义配置并恢复默认值，是否继续？",
            self,
        )
        if box.exec():
            if os.path.exists("config.ini"):
                os.remove("config.ini")
            ConfigManager._instance = None
            InfoBar.success("重置成功", "配置已恢复默认，重启程序后生效",
                            parent=self, position=InfoBarPosition.TOP, duration=3000)
