"""
PyQt6 runtime hook for PyInstaller.

Executed by the PyInstaller bootloader BEFORE any other code runs, so
we can pre-set the environment so that PyQt6's C extensions can find
their sibling Qt6 DLLs and platform plugins at import time.

Without this, you can hit one of:
  * ImportError: DLL load failed while importing QtCore:
      The specified procedure could not be found.
  * qt.qpa.plugin: Could not find the Qt platform plugin "windows" in ""
  * Missing Qt6Core.dll, Qt6Gui.dll, etc. at app startup

The hook uses os.add_dll_directory() (Python 3.8+ on Windows) to
register the Qt6 binary directory and the bundle root directory with
the Windows loader's secure DLL search set. Just modifying os.environ
['PATH'] does NOT work because modern Python uses LOAD_LIBRARY_SEARCH_
DEFAULT_DIRS which ignores PATH.
"""

import os
import sys


def _meipass() -> str:
    """Return the PyInstaller bundle directory, falling back to the script dir."""
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


bundle = _meipass()

# ── 1. Register the bundle root (_internal) so that VC++ runtime      ──
#    DLLs (VCRUNTIME140.dll, MSVCP140.dll) resolve from there.
if os.path.isdir(bundle):
    try:
        os.add_dll_directory(bundle)
    except OSError:
        pass

# ── 2. Register the Qt6 binary directory so that Qt6Core.dll,        ──
#    Qt6Gui.dll, Qt6Widgets.dll and their VC++ deps resolve when
#    PyQt6's .pyd files import them.
qt_bin = os.path.join(bundle, "PyQt6", "Qt6", "bin")
qt_plugins = os.path.join(bundle, "PyQt6", "Qt6", "plugins")
qt_platforms = os.path.join(qt_plugins, "platforms")

if os.path.isdir(qt_bin):
    try:
        os.add_dll_directory(qt_bin)
    except OSError:
        pass

# ── 3. Fallback: also prepend to PATH (older Python / homebrew Qt). ──
if os.path.isdir(qt_bin):
    os.environ["PATH"] = qt_bin + os.pathsep + os.environ.get("PATH", "")
if os.path.isdir(bundle):
    os.environ["PATH"] = bundle + os.pathsep + os.environ.get("PATH", "")

# ── 4. Tell Qt where to find its platform plugins.                  ──
if os.path.isdir(qt_plugins):
    os.environ["QT_PLUGIN_PATH"] = qt_plugins
if os.path.isdir(qt_platforms):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_platforms
