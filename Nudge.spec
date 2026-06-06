# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # Data files (appstate.json, tasks.json, groups.json, history.json) live
    # under %APPDATA%\Nudge\ at runtime — they are NOT bundled with the EXE.
    # Only static assets (icon) are included here.
    datas=[('icon.ico', '.')],
    # PyQt6.sip is the SIP runtime that PyQt6's generated bindings depend on;
    # PyInstaller's static analysis does not pick it up reliably, so we list
    # it (and the most commonly missed Qt submodules) explicitly.
    hiddenimports=[
        "PyQt6.sip",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
    ],
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
    name='Nudge',
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
    icon=['icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Nudge',
)
