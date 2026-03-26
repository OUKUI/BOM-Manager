# BOM 管理系统需求规格说明书

**日期**: 2026 年
**设计风格**: Microsoft Fluent Design (现代流程化)
**核心目标**: 构建一个高安全、可追溯、灵活且具备现代化用户体验的 BOM 管理工具。
**运行方式**: 单机桌面应用（Windows），SQLite 本地数据库

---

## 1. 用户界面与体验 (UI/UX)

### 1.1 设计风格
- **Fluent Design 语言**: 采用 Windows 11 设计语言，包含亚克力模糊效果 (Acrylic)、圆角卡片、平滑过渡动画、深度阴影。
- **流程化布局**:
  - **左侧**: 导航栏 (NavigationView)，支持图标 + 文字，底部显示用户信息与主题切换。
  - **顶部**: 命令栏 (CommandBar)，根据当前页面动态显示操作按钮 (新建、导入、导出等)。
  - **中部**: 内容区域，支持卡片式列表和树形表格。
  - **底部**: 状态栏，显示登录用户、角色、系统状态及提示信息。

### 1.2 主题与适配
- **深色/浅色模式**:
  - 内置一键切换功能 (太阳/月亮图标)。
  - 自动记忆用户偏好设置（写入 config.ini）。
  - 所有控件、图表、对话框均完美适配两种主题。
- **高 DPI 支持**:
  - 完美适配 4K 显示器及高分辨率屏幕 (150%-200% 缩放)。
  - 确保字体清晰、图标不模糊、布局不错位。

### 1.3 页面清单与原型

| 页面 | 导航图标 | 可见角色 | 核心功能 |
| :--- | :---: | :--- | :--- |
| 登录界面 | — | 全部 | 用户名/密码登录，首次登录强制改密 |
| 仪表盘 (Dashboard) | 🏠 | 全部 | 项目数量统计、最近编辑、快捷入口 |
| BOM 项目列表 | 📋 | 全部 | 搜索/筛选项目卡片，新建/打开/删除项目 |
| BOM 编辑器 | ✏️ | 超管/工程师 | 树形表格编辑 BOM 明细，拖拽调整层级 |
| BOM 历史版本 | 🕐 | 全部 | 查看变更履历，版本对比高亮差异 |
| 零件母表 | 🔩 | 全部(只读)/超管(编辑) | 搜索/新增/修改/导出零件信息 |
| 用户管理 | 👤 | 超管 | 增删改用户，重置密码，分配角色 |
| 审计日志 | 📜 | 超管(全部)/工程师(自己) | 操作记录查询，支持时间/类型/用户筛选 |
| 系统设置 | ⚙️ | 超管 | 数据库备份、主题、语言等设置 |

**BOM 编辑器布局原型**:
```
┌─────────────────────────────────────────────────────────────┐
│ [保存] [新增行] [删除行] [上移] [下移] [导入] [导出]  [历史版本▼] │
├──────────────────────────────────────────────────────────────┤
│ BOM编号: ED-72005-01  客户零件号: 98810-A2010  版本: A03      │
│ 建立日期: 2017-07-24  更新日期: 2024-08-13                    │
├─────┬──┬──────┬────────┬───────┬────────┬──┬────┬────────┤
│标记 │级│ 序号 │ 零件图号│ 零件版本│ 零件名称│规格│单位│用量│备注│
├─────┼──┼──────┼────────┼───────┼────────┼──┼────┼────────┤
│     │ 1│  1   │ED-72..│  A02  │刷卡充电│...│pcs│ 1  │    │
│  *  │ 2│  1.1 │ED-020..│  A01  │主体    │...│pcs│ 1  │    │
│     │ 2│  1.2 │ED-020..│  A01  │刷卡器  │...│pcs│ 1  │    │
│  ■  │ 3│1.2.1 │ED-080..│  A01  │弹片    │...│pcs│ 2  │    │
└─────┴──┴──────┴────────┴───────┴────────┴──┴────┴────────┘
```

---

## 2. 角色与权限体系 (RBAC)

系统定义三种核心角色，权限严格隔离：

| 功能模块 | 操作项 | 🔴 超级管理员 (Super Admin) | 🔵 工程师 (Engineer) | 🟢 查看者 (Viewer) |
| :--- | :--- | :---: | :---: | :---: |
| **用户管理** | 增删改查用户 | ✅ | ❌ | ❌ |
| | **重置/修改密码** | ✅ (**唯一权限**) | ❌ | ❌ |
| **零件母表** | **新增/修改/删除** | ✅ (**唯一权限**) | ❌ (仅只读) | ❌ |
| (Parts Master) | 查询/导出 | ✅ | ✅ | ✅ |
| **BOM 项目** | 创建新项目 | ✅ | ✅ | ❌ |
| | 编辑 BOM 结构/用量 | ✅ | ✅ (限授权项目) | ❌ |
| | 删除项目 | ✅ | ❌ | ❌ |
| | 导入/导出 Excel | ✅ | ✅ | ✅ (仅导出) |
| **系统日志** | 查看所有审计日志 | ✅ | ✅ (仅查看自己) | ❌ |

### 2.1 特殊安全策略
- **母表锁定**: 普通工程师无法直接修改零件母表。若需新增零件，必须提交申请或由超管录入。
- **密码管理特权**:
  - **禁止自助修改**: 普通用户界面**隐藏**"修改密码"入口。
  - **超管强制重置**: 仅超级管理员可在"用户管理"界面重置任意用户的密码。
  - **审计记录**: 所有密码重置操作必须记录详细日志 (操作人、目标用户、时间)。

---

## 3. 核心业务功能

### 3.1 灵活的层级管理
- **手动设定层级**: 不强制依赖父子关系自动计算，允许用户手动指定每个条目的 `level` (1, 2, 3...)。
- **视觉标记还原**: 支持自定义标记符号 (如 `*`, `■`, 数字等)，并在导出时保留这些视觉特征，以符合特定工艺文档规范。
- **拖拽/调整**: 支持在界面上直观地调整条目层级和顺序（上移/下移/升级/降级按钮）。

### 3.2 变更与版本追溯
- **变更履历表**:
  - 每次 BOM 保存前，强制弹出"填写变更原因"对话框（可选择跳过，视为草稿保存）。
  - 记录：序目、变更内容、变更原因、变更前版本、变更后版本、变更人、变更日期、备注。
- **历史回溯**: 支持查看项目的所有历史版本快照，并可对比不同版本间的差异（新增/删除/修改行高亮）。
- **版本号管理**: 同时管理"零件版本"（如 A01/A02）和"BOM 清单版本"（如 A03）。

### 3.3 数据导入与导出
- **导入流程**:
  1. 选择 Excel 文件（与现有模板格式一致）。
  2. 系统执行**预检报告**：校验列头、零件图号是否在母表中存在、格式是否正确。
  3. 预检通过后弹窗展示摘要，确认后正式写入数据库。
  4. 陌生零件（不在母表中）：标记为警告，允许用户选择"跳过"或"自动新增到母表（需超管权限）"。
- **导出格式**: 与 Excel 模板完全一致，包含变更履历表、头部信息、BOM 明细（自动 VLOOKUP 还原、缩进层级、标记符号、样式）。

### 3.4 数据结构完整性
- **全字段覆盖**:
  - 头部信息: BOM 编号、客户零件号、客户描述、建立日期、更新日期、当前版本。
  - 明细信息: 层级标记、层级标志、序号、零件图号、零件版本、零件名称、规格/材料、单位、用量、备注。
  - 变更履历: 序目、变更内容、变更原因、变更前版本、变更后版本、变更人、变更日期、备注。

---

## 4. 数据安全与审计

### 4.1 软删除机制 (Soft Delete)
- 所有关键数据 (用户、项目、零件、BOM 条目) **严禁物理删除**。
- 通过 `is_deleted` 标记位实现逻辑删除，确保数据永远可恢复、可审计。

### 4.2 全链路审计日志 (Audit Logs)
- **记录范围**:
  - 数据变更 (增删改 BOM、修改母表)。
  - 敏感操作 (重置密码、权限变更)。
  - 系统事件 (登录成功/失败、导出操作)。
- **日志内容**: 操作人、操作时间、操作类型、受影响资源类型/ID、变更前数据 (JSON)、变更后数据 (JSON)。

### 4.3 密码安全
- **加密存储**: 所有密码使用 `bcrypt` 哈希存储，严禁明文。
- **复杂度校验**: 超管重置密码时，系统强制校验密码强度（最少 8 位，含大小写字母+数字）。
- **首次登录**: 系统初始化时自动创建默认超管账户，首次登录后强制修改密码。

---

## 5. 数据库设计 (SQLite + SQLAlchemy)

### 5.1 数据模型总览

```
users ────────────────────────────────────┐
  │ created_by/updated_by                 │
  ▼                                       │
parts_master                              │
  │ part_number (FK in bom_items)         │
  ▼                                       │
bom_projects ──── bom_items              │
  │                 │ part snapshot        │
  │                 └── (JSON 快照)        │
  ▼                                       │
bom_change_logs                          │
  │ changed_by (FK users) ───────────────┘
audit_logs
  └── operator_id (FK users)
```

### 5.2 表结构详细定义

#### 表 1: `users` — 用户表

| 字段 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | TEXT (UUID) | PK | 用户唯一标识 |
| username | TEXT | UNIQUE, NOT NULL | 登录用户名 |
| password_hash | TEXT | NOT NULL | bcrypt 哈希值 |
| role | TEXT | NOT NULL | `super_admin` / `engineer` / `viewer` |
| display_name | TEXT | NOT NULL | 显示名称 |
| must_change_pwd | INTEGER | DEFAULT 1 | 1=下次登录需改密 |
| is_deleted | INTEGER | DEFAULT 0 | 软删除标记 |
| created_at | TEXT | NOT NULL | ISO8601 时间戳 |
| updated_at | TEXT | NOT NULL | ISO8601 时间戳 |
| last_login_at | TEXT | — | 最后登录时间 |

#### 表 2: `parts_master` — 零件母表

| 字段 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PK AUTOINCREMENT | 内部 ID |
| part_number | TEXT | UNIQUE, NOT NULL | 零件图号，如 `ED-15302-01` |
| version | TEXT | NOT NULL | 零件版本，如 `A03` |
| standard_level | TEXT | — | 零件标准，如 `主要` / `要` / `次要` |
| name | TEXT | NOT NULL | 零件名称 |
| spec_material | TEXT | — | 规格/材料 |
| unit | TEXT | — | 单位，如 `pcs` |
| default_qty | REAL | DEFAULT 1 | 默认用量 |
| notes | TEXT | — | 备注 |
| is_deleted | INTEGER | DEFAULT 0 | 软删除标记 |
| created_by | TEXT | FK users.id | 创建人 |
| updated_by | TEXT | FK users.id | 最后修改人 |
| created_at | TEXT | NOT NULL | ISO8601 时间戳 |
| updated_at | TEXT | NOT NULL | ISO8601 时间戳 |

#### 表 3: `bom_projects` — BOM 项目表

| 字段 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | TEXT (UUID) | PK | 项目唯一标识 |
| bom_number | TEXT | NOT NULL | BOM 编号，如 `ED-72005-01` |
| customer_part_number | TEXT | — | 客户零件号，如 `98810-A2010` |
| customer_description | TEXT | — | 客户描述（对应 Excel 客户零件号旁的描述文本） |
| project_name | TEXT | — | 内部项目名称 |
| current_version | TEXT | NOT NULL | 当前 BOM 版本，如 `A03` |
| established_date | TEXT | NOT NULL | 建立日期 |
| updated_date | TEXT | NOT NULL | 更新日期 |
| status | TEXT | DEFAULT 'active' | `active` / `archived` |
| is_deleted | INTEGER | DEFAULT 0 | 软删除标记 |
| created_by | TEXT | FK users.id | 创建人 |
| updated_by | TEXT | FK users.id | 最后修改人 |
| created_at | TEXT | NOT NULL | ISO8601 时间戳 |
| updated_at | TEXT | NOT NULL | ISO8601 时间戳 |

#### 表 4: `bom_items` — BOM 明细表

| 字段 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PK AUTOINCREMENT | 内部 ID |
| bom_project_id | TEXT | FK bom_projects.id | 所属项目 |
| sort_order | INTEGER | NOT NULL | 排序号（决定行显示顺序） |
| level | INTEGER | NOT NULL | 层级深度，如 1/2/3 |
| level_mark | TEXT | — | 层级标记符号，如 `*`、`■`、空 |
| level_label | TEXT | — | 层级标志文字，如 `一`、`二`、`三` |
| part_number | TEXT | NOT NULL | 零件图号（关联 parts_master） |
| part_snapshot | TEXT | — | JSON 快照（保存时零件的版本/名称/规格等，用于历史还原） |
| quantity | REAL | DEFAULT 1 | 用量 |
| notes | TEXT | — | 备注 |
| is_deleted | INTEGER | DEFAULT 0 | 软删除标记 |
| created_by | TEXT | FK users.id | 创建人 |
| created_at | TEXT | NOT NULL | ISO8601 时间戳 |
| updated_at | TEXT | NOT NULL | ISO8601 时间戳 |

#### 表 5: `bom_change_logs` — 变更履历表

| 字段 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PK AUTOINCREMENT | 内部 ID |
| bom_project_id | TEXT | FK bom_projects.id | 所属项目 |
| sequence | INTEGER | NOT NULL | 序目（变更序号） |
| change_description | TEXT | — | 变更内容 |
| change_reason | TEXT | NOT NULL | 变更原因 |
| previous_version | TEXT | — | 变更前版本 |
| new_version | TEXT | NOT NULL | 变更后版本 |
| changed_by | TEXT | FK users.id | 变更人 |
| change_date | TEXT | NOT NULL | 变更日期 |
| notes | TEXT | — | 备注 |
| bom_snapshot | TEXT | — | 变更时 BOM 明细的完整 JSON 快照（用于历史回溯） |

#### 表 6: `audit_logs` — 系统审计日志

| 字段 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PK AUTOINCREMENT | 内部 ID |
| operator_id | TEXT | FK users.id | 操作人 ID |
| operator_name | TEXT | NOT NULL | 操作人姓名快照 |
| operation_type | TEXT | NOT NULL | 见下方操作类型枚举 |
| resource_type | TEXT | — | `USER` / `PART` / `BOM` / `BOM_ITEM` |
| resource_id | TEXT | — | 受影响资源的 ID |
| data_before | TEXT | — | 变更前数据 (JSON) |
| data_after | TEXT | — | 变更后数据 (JSON) |
| detail | TEXT | — | 补充说明文字 |
| created_at | TEXT | NOT NULL | ISO8601 时间戳 |

**操作类型枚举** (`operation_type`):
`LOGIN_SUCCESS` / `LOGIN_FAIL` / `LOGOUT` / `CREATE` / `UPDATE` / `SOFT_DELETE` / `RESTORE` / `EXPORT` / `IMPORT` / `RESET_PASSWORD` / `CHANGE_ROLE`

---

## 6. Excel 模板规范

> 以现有文件 `00-4mm-BoM-标准-202603的副本.xlsm` 为基准。

### 6.1 工作簿结构

| Sheet 名称 | 用途 |
| :--- | :--- |
| `零部件总览表` | 零件母表数据（831+ 行，8列有效列） |
| `standard` | 空白 BOM 模板（用于新建项目时复制） |
| `[项目代号]` | 各具体 BOM 项目工作表（如 AD02、AP32-2pin） |

**导出策略**: 系统导出时生成独立的 `.xlsx` 文件（不含 VBA），每个项目一个 Sheet，格式与原 `.xlsm` 一致。

### 6.2 零部件总览表列定义

| 列 | 列号 | 字段名 | 示例 |
| :--- | :---: | :--- | :--- |
| A | 1 | 零件图号 | `ED-15302-01` |
| B | 2 | 零件版本 | `A03` |
| C | 3 | 零件标准 | `主要` / `要` / `次要` |
| D | 4 | 零件名称 | `刷卡充电` |
| E | 5 | 规格/材料 | `DC56D+Z 1.8mm-144 铁板` |
| F | 6 | 单位 | `pcs` |
| G | 7 | 用量 | `1` |
| H | 8 | 备注 | — |

### 6.3 BOM 工作表布局

```
行1:    [变更履历表标题]  (合并单元格，跨全宽)
行2:    序目 | 变更内容 | | | | | 变更原因 | | 变更前版本 | 变更后版本 | 变更人 | 变更日期 | 备注
行3~5:  变更记录（最多3条最新记录显示于此）
行6:    [空行]
行7:    BOM编号 | | | | | 客户零件号 | [客户描述] | | | | | 建立日期 | [日期]
行8:    [图号值] | | | | | [客户零件号值] | | | | | | 更新日期 | [日期]
行9:    [零件图号] | | | | | | | 版本 | [版本号]
行10:   [列标题行]: 标记 | 层级 | 序号 | ... | 零件图号 | 零件版本 | 零件标准 | 零件名称 | 规格/材料 | 单位 | 用量 | 备注
行11+:  BOM 明细数据行
```

**BOM 明细行列对应**:

| 列 | 内容 | 说明 |
| :--- | :--- | :--- |
| A | 层级标记 | `*`（重要）/ `■`（特殊）/ 空（普通） |
| B | 层级标志 | `一`/`二`/`三`（中文层级标签）/ 空 |
| C~E | — | 保留/合并列 |
| F | 零件图号 | 手动填写，关联母表 |
| G | 零件版本 | `=VLOOKUP($F行, 零部件总览表!$A:$H, 2, FALSE)` |
| H | 零件标准 | `=VLOOKUP(...)` col 3 |
| I | 零件名称 | `=VLOOKUP(...)` col 4 |
| J | 规格/材料 | `=VLOOKUP(...)` col 5 |
| K | 单位 | `=VLOOKUP(...)` col 6 |
| L | 用量 | `=VLOOKUP(...)` col 7（或手动覆盖） |
| M | 备注 | `=VLOOKUP(...)` col 8 |

---

## 7. 项目目录结构

```
bom_manager/
│
├── main.py                        # 程序入口，初始化 Qt App，加载主窗口
├── config.ini                     # 用户配置（主题、窗口尺寸、数据库路径）
├── requirements.txt               # Python 依赖清单
├── build.spec                     # PyInstaller 打包配置
│
├── app/
│   │
│   ├── core/                      # 核心横切关注点
│   │   ├── __init__.py
│   │   ├── auth.py                # 登录认证、会话管理（当前登录用户单例）
│   │   ├── rbac.py                # 权限拦截装饰器 @require_role(...)
│   │   └── audit.py               # 审计日志写入工具函数
│   │
│   ├── models/                    # SQLAlchemy ORM 数据模型
│   │   ├── __init__.py
│   │   ├── base.py                # DeclarativeBase + SoftDeleteMixin + TimestampMixin
│   │   ├── user.py                # User 模型
│   │   ├── part.py                # PartsMaster 模型
│   │   ├── bom.py                 # BomProject + BomItem 模型
│   │   └── log.py                 # BomChangeLog + AuditLog 模型
│   │
│   ├── services/                  # 业务逻辑层（不含 UI 代码）
│   │   ├── __init__.py
│   │   ├── user_service.py        # 用户增删改查、密码重置
│   │   ├── part_service.py        # 零件母表管理
│   │   ├── bom_service.py         # BOM 项目和明细管理、版本快照
│   │   └── excel_service.py       # Excel 导入（含预检）& 导出（格式化）
│   │
│   ├── ui/                        # 界面层 (PySide6 + QFluentWidgets)
│   │   ├── __init__.py
│   │   ├── main_window.py         # 主窗口：NavigationView + CommandBar + 状态栏
│   │   ├── login_window.py        # 登录窗口
│   │   │
│   │   ├── pages/                 # 各主页面（对应导航项）
│   │   │   ├── __init__.py
│   │   │   ├── dashboard_page.py          # 仪表盘
│   │   │   ├── bom_list_page.py           # BOM 项目列表
│   │   │   ├── bom_editor_page.py         # BOM 树形编辑器
│   │   │   ├── bom_history_page.py        # 变更历史与版本对比
│   │   │   ├── parts_master_page.py       # 零件母表
│   │   │   ├── user_management_page.py    # 用户管理（仅超管可见）
│   │   │   ├── audit_log_page.py          # 审计日志
│   │   │   └── settings_page.py           # 系统设置
│   │   │
│   │   ├── dialogs/               # 弹出对话框
│   │   │   ├── __init__.py
│   │   │   ├── change_reason_dialog.py    # 保存 BOM 时填写变更原因
│   │   │   ├── import_preview_dialog.py   # 导入预检报告确认框
│   │   │   ├── add_part_dialog.py         # 新增/编辑零件
│   │   │   ├── add_bom_dialog.py          # 新建 BOM 项目
│   │   │   └── reset_password_dialog.py   # 超管重置用户密码
│   │   │
│   │   └── components/            # 可复用 UI 组件
│   │       ├── __init__.py
│   │       ├── bom_tree_widget.py          # 树形表格（支持拖拽、层级缩进）
│   │       ├── diff_viewer_widget.py       # BOM 版本差异高亮对比控件
│   │       └── status_bar_widget.py        # 底部状态栏（用户/角色/提示）
│   │
│   └── utils/                     # 工具函数
│       ├── __init__.py
│       ├── db.py                  # 数据库 Session 管理（get_session, init_db）
│       ├── security.py            # bcrypt 哈希/验证、密码强度校验
│       └── validators.py          # 输入校验（零件图号格式、版本号格式等）
│
├── data/                          # 运行时数据（自动创建，勿手动修改）
│   └── bom.db                     # SQLite 数据库文件
│
├── logs/                          # 审计日志文本备份（自动创建）
│   └── audit_YYYYMMDD.log
│
├── templates/                     # Excel 导出基础模板
│   └── bom_export_template.xlsx   # 含列宽/样式/标题的空白模板
│
└── tests/                         # 单元与集成测试
    ├── conftest.py                 # 测试用内存 SQLite 数据库 fixture
    ├── test_services/
    │   ├── test_user_service.py
    │   ├── test_part_service.py
    │   ├── test_bom_service.py
    │   └── test_excel_service.py
    └── test_models/
        └── test_soft_delete.py
```

---

## 8. 模块架构说明

### 8.1 分层架构

```
┌─────────────────────────────────────────┐
│              UI 层 (app/ui/)             │  ← 仅负责展示与交互，不含业务逻辑
├─────────────────────────────────────────┤
│           服务层 (app/services/)         │  ← 业务逻辑、权限校验、事务管理
├─────────────────────────────────────────┤
│           模型层 (app/models/)           │  ← ORM 定义、软删除、时间戳 Mixin
├─────────────────────────────────────────┤
│        数据库 (SQLite via SQLAlchemy)    │  ← data/bom.db
└─────────────────────────────────────────┘
         ↕ 横切关注点 (app/core/)
    auth.py / rbac.py / audit.py
```

### 8.2 关键设计决策

| 决策点 | 选择 | 原因 |
| :--- | :--- | :--- |
| 会话管理 | 全局单例 `AuthContext` | 桌面单用户场景，避免传参复杂性 |
| 权限拦截 | 装饰器 `@require_role` | 服务层统一拦截，UI 层仅控制按钮可见性 |
| 历史快照 | JSON 字段存于 `bom_change_logs.bom_snapshot` | 无需复杂版本表，直接序列化整个 BOM 明细 |
| Excel 导出 | `openpyxl` 写新文件（不用模板的 VBA） | 避免 xlsm 依赖，纯 xlsx 更通用 |
| 零件数据一致性 | BOM 明细保存时写入 `part_snapshot` JSON | 零件母表更新后，历史 BOM 数据仍可还原 |

### 8.3 核心流程：保存 BOM

```
用户点击[保存]
    │
    ▼
BomEditorPage.on_save_clicked()
    │ 收集当前树形表格数据
    ▼
ChangeReasonDialog.exec()  ← 弹出填写变更原因
    │ 用户填写并确认
    ▼
BomService.save_bom(project_id, items, change_info)
    │
    ├── 1. 校验权限 @require_role('engineer', 'super_admin')
    ├── 2. 对每个 item，读取 parts_master 写入 part_snapshot
    ├── 3. 软删除旧 bom_items，插入新 bom_items
    ├── 4. 写入 bom_change_logs（含 bom_snapshot JSON）
    ├── 5. 更新 bom_projects.current_version & updated_date
    └── 6. 写入 audit_logs（UPDATE, resource_type=BOM）
```

---

## 9. 配置管理

配置文件路径: `config.ini`（与 `main.py` 同级，首次运行自动生成）

```ini
[app]
theme = light          ; light / dark
language = zh_CN
window_width = 1280
window_height = 800
window_maximized = false

[database]
path = data/bom.db

[security]
session_timeout_minutes = 480   ; 8小时自动退出（预留，当前单机不强制）
min_password_length = 8

[export]
default_export_dir = exports/
author_name =          ; 导出 Excel 时写入的作者信息
```

---

## 10. 技术栈 (2026 标准)

| 类别 | 选型 | 版本要求 |
| :--- | :--- | :--- |
| GUI 框架 | `PySide6` | ≥ 6.7 |
| UI 组件库 | `PyQt-Fluent-Widgets` (QFluentWidgets) | 最新稳定版 |
| 数据库 ORM | `SQLAlchemy` | ≥ 2.0 |
| 数据库驱动 | 内置 `sqlite3` | — |
| Excel 处理 | `openpyxl` | ≥ 3.1 |
| 密码安全 | `bcrypt` | ≥ 4.0 |
| 打包工具 | `PyInstaller` | ≥ 6.0 |
| 测试框架 | `pytest` | ≥ 8.0 |

**requirements.txt 草稿**:
```
PySide6>=6.7.0
PyQt-Fluent-Widgets>=1.7.0
SQLAlchemy>=2.0.0
openpyxl>=3.1.0
bcrypt>=4.0.0
```

---

## 11. 打包与发布

### 11.1 PyInstaller 打包策略
- 打包为单目录模式（`--onedir`），便于用户定位 `data/` 和 `config.ini`。
- 包含 `templates/` 目录和 QFluentWidgets 所需资源。
- 输出目录: `dist/BOM管理系统/`

### 11.2 首次运行初始化
程序启动时检测 `data/bom.db` 是否存在：
- **不存在**: 自动执行建库脚本，创建所有表，插入默认超管账户（用户名: `admin`，密码: `Admin@1234`，`must_change_pwd=1`）。
- **已存在**: 执行 Schema 迁移检查（比较表结构版本号）。

### 11.3 数据备份
- 系统设置页面提供"立即备份"按钮，将 `bom.db` 复制为 `bom_backup_YYYYMMDD_HHMMSS.db`。
- 可选设置每次启动时自动备份最近一份（保留最近 7 份）。

---

## 12. 开发阶段规划

### 第一阶段：基础架构（里程碑 M1）
- [ ] 搭建项目目录结构，配置 `requirements.txt`。
- [ ] 实现数据库 ORM 模型（6张表，含软删除/时间戳 Mixin）。
- [ ] 实现首次运行初始化脚本（建库 + 创建默认超管）。
- [ ] 搭建 QFluentWidgets 主窗口框架（NavigationView、主题切换、高 DPI）。
- [ ] 实现登录窗口与 `AuthContext` 会话管理。
- [ ] 实现 `@require_role` 权限装饰器。

### 第二阶段：核心业务（里程碑 M2）
- [ ] 零件母表页面（超管编辑 + 全员只读 + 搜索 + 导出）。
- [ ] BOM 项目列表页面（新建/打开/归档/删除）。
- [ ] BOM 树形编辑器（层级标记、手动层级、拖拽排序）。
- [ ] 保存 BOM 流程（变更原因弹窗 + part_snapshot + bom_change_logs）。
- [ ] 用户管理页面（超管：增删改 + 密码重置）。

### 第三阶段：数据交互与审计（里程碑 M3）
- [ ] Excel 导入（预检报告弹窗 + 陌生零件处理策略）。
- [ ] Excel 导出（格式还原：层级缩进 + 标记符号 + 变更履历 + 样式）。
- [ ] BOM 历史版本查看与差异对比（行级高亮：新增/删除/修改）。
- [ ] 审计日志查询页面（分页 + 多维度筛选）。
- [ ] 仪表盘统计卡片。
- [ ] PyInstaller 打包测试与发布。

---

> **备注**: 本系统专为对数据安全、版本追溯及界面美观度有极高要求的制造业环境设计。所有设计决策均围绕"防错"、"可控"与"高效"展开。数据库以 SQLite 单机部署，后续如需多用户并发可迁移至 PostgreSQL（SQLAlchemy ORM 层无需改动）。
