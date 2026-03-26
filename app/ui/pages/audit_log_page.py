"""
审计日志页面：分页查询 + 多维度筛选
超管：全部日志  工程师：仅自己的操作
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, CaptionLabel, SearchLineEdit, ComboBox,
    PushButton, FluentIcon, InfoBar, InfoBarPosition, TableWidget,
)
from app.core.auth import AuthContext
from app.models import AuditLog
from app.utils.db import get_session

PAGE_SIZE = 50


class AuditLogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AuditLogPage")
        self._page = 0
        self._total = 0
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 36, 36, 20)
        root.setSpacing(12)

        root.addWidget(TitleLabel("审计日志"))

        # 筛选栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._search = SearchLineEdit(self)
        self._search.setPlaceholderText("搜索操作人/资源ID/详情")
        self._search.setFixedWidth(240)
        toolbar.addWidget(self._search)

        self._op_filter = ComboBox(self)
        self._op_filter.addItems(["全部操作", "LOGIN_SUCCESS", "LOGIN_FAIL",
                                   "CREATE", "UPDATE", "SOFT_DELETE", "EXPORT",
                                   "IMPORT", "RESET_PASSWORD"])
        self._op_filter.setFixedWidth(160)
        toolbar.addWidget(self._op_filter)

        self._res_filter = ComboBox(self)
        self._res_filter.addItems(["全部资源", "USER", "PART", "BOM", "BOM_ITEM", "DB"])
        self._res_filter.setFixedWidth(120)
        toolbar.addWidget(self._res_filter)

        btn_search = PushButton(FluentIcon.SEARCH, "查询", self)
        btn_search.clicked.connect(lambda: self._load(reset=True))
        toolbar.addWidget(btn_search)

        toolbar.addStretch()

        btn_prev = PushButton(FluentIcon.PAGE_LEFT, "", self)
        btn_prev.setFixedWidth(36)
        btn_prev.clicked.connect(self._prev_page)
        toolbar.addWidget(btn_prev)

        self._page_label = CaptionLabel("第 1 页")
        toolbar.addWidget(self._page_label)

        btn_next = PushButton(FluentIcon.PAGE_RIGHT, "", self)
        btn_next.setFixedWidth(36)
        btn_next.clicked.connect(self._next_page)
        toolbar.addWidget(btn_next)

        root.addLayout(toolbar)

        # 表格
        cols = ["时间", "操作人", "操作类型", "资源类型", "资源ID", "详情"]
        self._table = TableWidget(self)
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Stretch)
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        root.addWidget(self._table)

        self._count_label = CaptionLabel("共 0 条")
        root.addWidget(self._count_label)

    def _load(self, reset: bool = False):
        if reset:
            self._page = 0

        ctx = AuthContext()
        keyword = self._search.text().strip()
        op_type = self._op_filter.currentText()
        res_type = self._res_filter.currentText()

        with get_session() as s:
            q = s.query(AuditLog)
            # 工程师只看自己
            if ctx.role == "engineer" and ctx.user:
                q = q.filter(AuditLog.operator_id == ctx.user.id)
            if op_type and op_type != "全部操作":
                q = q.filter(AuditLog.operation_type == op_type)
            if res_type and res_type != "全部资源":
                q = q.filter(AuditLog.resource_type == res_type)
            if keyword:
                from sqlalchemy import or_
                kw = f"%{keyword}%"
                q = q.filter(or_(
                    AuditLog.operator_name.ilike(kw),
                    AuditLog.resource_id.ilike(kw),
                    AuditLog.detail.ilike(kw),
                ))
            self._total = q.count()
            logs = (
                q.order_by(AuditLog.created_at.desc())
                .offset(self._page * PAGE_SIZE)
                .limit(PAGE_SIZE)
                .all()
            )

        self._table.setRowCount(0)
        for log in logs:
            row = self._table.rowCount()
            self._table.insertRow(row)
            ts = log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else ""
            for col, val in enumerate([
                ts,
                log.operator_name or "",
                log.operation_type or "",
                log.resource_type or "",
                log.resource_id or "",
                log.detail or "",
            ]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self._table.setItem(row, col, item)

        total_pages = max(1, (self._total + PAGE_SIZE - 1) // PAGE_SIZE)
        self._page_label.setText(f"第 {self._page + 1} / {total_pages} 页")
        self._count_label.setText(f"共 {self._total} 条")

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._load()

    def _next_page(self):
        total_pages = (self._total + PAGE_SIZE - 1) // PAGE_SIZE
        if self._page < total_pages - 1:
            self._page += 1
            self._load()
