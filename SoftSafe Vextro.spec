# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\UNKVOICES\\DEVELOPER TOOL\\Projects\\YT-DLP\\main.py'],
    pathex=[],
    binaries=[('D:\\UNKVOICES\\DEVELOPER TOOL\\Projects\\YT-DLP\\ffmpeg.exe', '.')],
    datas=[('D:\\UNKVOICES\\DEVELOPER TOOL\\Projects\\YT-DLP\\ico.png', '.'), ('D:\\UNKVOICES\\DEVELOPER TOOL\\Projects\\YT-DLP\\exit.png', '.')],
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
    a.binaries,
    a.datas,
    [],
    name='SoftSafe Vextro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='D:\\UNKVOICES\\DEVELOPER TOOL\\Projects\\YT-DLP\\version_info.txt',
    icon=['D:\\UNKVOICES\\DEVELOPER TOOL\\Projects\\YT-DLP\\ico.ico'],
)
