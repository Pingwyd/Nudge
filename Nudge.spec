# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

# Pull in every PyQt6 submodule, binary, and data file. PyQt6's Qt
# distribution is fragmented across `PyQt6` and the split `PyQt6-Qt6`
# wheel — `collect_all` ensures we get all of it so Qt's loader can
# resolve its siblings at runtime.
pyqt6_datas, pyqt6_binaries, pyqt6_hiddenimports = collect_all("PyQt6")

# winotify is used for the boot-time toast notification; make sure its
# native bits are bundled too.
winotify_datas, winotify_binaries, winotify_hiddenimports = collect_all("winotify")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=pyqt6_binaries + winotify_binaries,
    # Data files (appstate.json, tasks.json, groups.json, history.json) live
    # under %APPDATA%\Nudge\ at runtime — they are NOT bundled with the EXE.
    # Only static assets (icon) are included here.
    datas=[('icon.ico', '.')] + pyqt6_datas + winotify_datas,
    # PyQt6.sip is the SIP runtime that PyQt6's generated bindings depend on;
    # PyInstaller's static analysis does not pick it up reliably, so we list
    # it (and the most commonly missed Qt submodules) explicitly. The
    # `collect_all("PyQt6")` call above also contributes PyQt6 submodules.
    hiddenimports=[
        "PyQt6.sip",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
    ] + pyqt6_hiddenimports + winotify_hiddenimports,
    hookspath=[],
    hooksconfig={},
    # The runtime hook sets up Qt library / plugin paths before PyQt6
    # imports happen — fixes "DLL load failed while importing QtCore".
    runtime_hooks=['pyqt6_runtime_hook.py'],
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
