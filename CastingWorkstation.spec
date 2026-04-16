# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


conda_bin = Path(r"C:\ProgramData\anaconda3\Library\bin")
required_dlls = [
    "ffi.dll",
    "libbz2.dll",
    "libexslt.dll",
    "liblzma.dll",
    "libxml2.dll",
    "libxslt.dll",
    "sqlite3.dll",
]

binaries = [
    (str(conda_bin / dll_name), ".")
    for dll_name in required_dlls
    if (conda_bin / dll_name).exists()
]

datas = [
    (r"E:\zhuzaochuangxin\casting_workstation\app\core\db\schema.sql", r"app\core\db"),
]


a = Analysis(
    ['E:\\zhuzaochuangxin\\casting_workstation\\\\app\\\\main.py'],
    pathex=['E:\\zhuzaochuangxin\\casting_workstation'],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CastingWorkstation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CastingWorkstation',
)
