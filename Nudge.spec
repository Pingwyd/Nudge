# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

# `PyQt6.sip` is a namespace module that, in PyQt6 >= 6.6.1, is
# actually shipped by the `pyqt6-sip` (PyPI: `pyqt6-sip`,
# distribution: `pyqt6_sip`) package, not by `PyQt6` itself.
# `collect_all("PyQt6")` does NOT see it, so we have to pull it in
# explicitly. Without this the EXE crashes with:
#   ModuleNotFoundError: No module named 'PyQt6.sip'
#
# On PyQt6 < 6.7 the SIP module is bundled into the `PyQt6` wheel
# and this collect_all is a no-op (PyInstaller just warns that
# `pyqt6-sip` is not a package). That's fine — the explicit
# `PyQt6.sip` in hiddenimports below covers that case.
pyqt6sip_datas, pyqt6sip_binaries, pyqt6sip_hiddenimports = collect_all("pyqt6-sip")

# `PyQt6` proper — every Qt submodule, Qt6 binary, and data file.
pyqt6_datas, pyqt6_binaries, pyqt6_hiddenimports = collect_all("PyQt6")

# --- Critical Qt6 DLLs: ALSO deploy them right next to the .pyd files ---
# collect_all("PyQt6") puts the Qt6 DLLs inside _internal/PyQt6/Qt6/bin/.
# But Python 3.8+ on Windows uses LOAD_LIBRARY_SEARCH_DEFAULT_DIRS which
# only searches the .pyd's own directory, system32, and directories
# registered via os.add_dll_directory(). PATH is ignored.
#
# The runtime hook (pyqt6_runtime_hook.py) calls os.add_dll_directory()
# for Qt6/bin, but to be absolutely sure we also make a direct copy of
# the essential DLLs right next to QtCore.pyd/QtGui.pyd/QtWidgets.pyd,
# so the OS-level loader finds them naturally without ANY path fix.
import importlib.util
_pyqt6_spec = importlib.util.find_spec("PyQt6")
if _pyqt6_spec is not None and _pyqt6_spec.origin is not None:
    _qt6_bin_dir = Path(_pyqt6_spec.origin).parent / "Qt6" / "bin"
    _ESSENTIAL_QT_DLLS: tuple[str, ...] = (
        "Qt6Core.dll",
        "Qt6Gui.dll",
        "Qt6Widgets.dll",
        "VCRUNTIME140.dll",
        "VCRUNTIME140_1.dll",
        "MSVCP140.dll",
        "MSVCP140_1.dll",
        "MSVCP140_2.dll",
        "concrt140.dll",
    )
    for _dll_name in _ESSENTIAL_QT_DLLS:
        _src = _qt6_bin_dir / _dll_name
        if _src.is_file():
            # PyInstaller binary TOC entries are 2-tuples:
            #   (absolute_source_path, relative_dest_dir)
            # This places the DLL at _internal/PyQt6/<dll_name>
            # — right next to QtCore.pyd, QtGui.pyd etc.
            pyqt6_binaries.append((os.fspath(_src), "PyQt6"))

# Submodules the app code statically references. `collect_all` already
# returns the visible submodules; this list covers the commonly missed
# ones that are only reachable via fully-qualified names.
pyqt6_extra_hidden = collect_submodules("PyQt6")

# winotify is used for the boot-time toast notification; make sure its
# native bits are bundled too.
winotify_datas, winotify_binaries, winotify_hiddenimports = collect_all("winotify")

# Qt subsystems Nudge does NOT use. Excluding them keeps the bundle
# smaller and silences "Library not found" warnings for unrelated Qt
# plugins (Qt3D, QML compiler, designer translations, etc.).
qt_excludes = [
    "PyQt6.Qt3DAnimation",
    "PyQt6.Qt3DCore",
    "PyQt6.Qt3DExtras",
    "PyQt6.Qt3DInput",
    "PyQt6.Qt3DLogic",
    "PyQt6.Qt3DRender",
    "PyQt6.QtBluetooth",
    "PyQt6.QtDBus",
    "PyQt6.QtDesigner",
    "PyQt6.QtHelp",
    "PyQt6.QtMultimedia",
    "PyQt6.QtMultimediaWidgets",
    "PyQt6.QtNfc",
    "PyQt6.QtOpenGL",
    "PyQt6.QtOpenGLWidgets",
    "PyQt6.QtPdf",
    "PyQt6.QtPdfWidgets",
    "PyQt6.QtPositioning",
    "PyQt6.QtQml",
    "PyQt6.QtQuick",
    "PyQt6.QtQuick3D",
    "PyQt6.QtQuickWidgets",
    "PyQt6.QtRemoteObjects",
    "PyQt6.QtSensors",
    "PyQt6.QtSerialPort",
    "PyQt6.QtSpatialAudio",
    "PyQt6.QtSql",
    "PyQt6.QtSvgWidgets",
    "PyQt6.QtTest",
    "PyQt6.QtTextToSpeech",
    "PyQt6.QtWebChannel",
    "PyQt6.QtWebSockets",
    "PyQt6.QtXml",
    "PyQt6.QtLocation",
    "PyQt6.QtNetwork",
    "PyQt6.QtSvg",
    "PyQt6.QtWebEngine",
    "PyQt6.QtWebEngineCore",
    "PyQt6.QtWebEngineWidgets",
    "tkinter",
    "test",
    "distutils",
    "setuptools",
    "pip",
    "numpy",
    "pandas",
    "matplotlib",
    "scipy",
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=pyqt6_binaries + pyqt6sip_binaries + winotify_binaries,
    # Data files (appstate.json, tasks.json, groups.json, history.json) live
    # under %APPDATA%\Nudge\ at runtime — they are NOT bundled with the EXE.
    # Only static assets (icon) are included here.
    datas=[('icon.ico', '.')] + pyqt6_datas + pyqt6sip_datas + winotify_datas,
    hiddenimports=[
        # SIP runtime — PyQt6's generated bindings import PyQt6.sip at
        # module load time. Must come first.
        "PyQt6.sip",
        # Qt submodules the app statically imports.
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
    ]
    + pyqt6_extra_hidden
    + pyqt6_hiddenimports
    + pyqt6sip_hiddenimports
    + winotify_hiddenimports,
    hookspath=[],
    hooksconfig={},
    # The runtime hook sets up Qt library / plugin paths before PyQt6
    # imports happen — fixes "DLL load failed while importing QtCore".
    runtime_hooks=['pyqt6_runtime_hook.py'],
    excludes=qt_excludes,
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
    strip=True,
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
    strip=True,
    upx=True,
    upx_exclude=[],
    name='Nudge',
)
