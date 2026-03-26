# -*- mode: python ; coding: utf-8 -*-
"""
BOM 管理系统 PyInstaller 打包配置
运行方式：pyinstaller build.spec
输出目录：dist/BOM管理系统/
"""
import os

block_cipher = None

# QFluentWidgets 资源路径
import qfluentwidgets
fluent_pkg_dir = os.path.dirname(qfluentwidgets.__file__)

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # QFluentWidgets 图标与资源
        (os.path.join(fluent_pkg_dir, 'resource'), 'qfluentwidgets/resource'),
        # 本项目模板文件
        ('templates', 'templates'),
    ],
    hiddenimports=[
        'qfluentwidgets',
        'sqlalchemy.dialects.sqlite',
        'bcrypt',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'app',
        'app.core',
        'app.models',
        'app.services',
        'app.ui',
        'app.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BOM管理系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # 可替换为 'assets/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BOM管理系统',     # dist/ 下的目录名
)
