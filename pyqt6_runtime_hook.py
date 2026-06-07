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

The hook adjusts:
  * PATH         — so Qt6Core.dll, MSVCP140.dll, VCRUNTIME140.dll, etc. resolve
  * QT_PLUGIN_PATH, QT_QPA_PLATFORM_PLUGIN_PATH — so Qt can find its plugins
"""

import os
import sys


def _meipass() -> str:
    """Return the PyInstaller bundle directory, falling back to the script dir."""
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


bundle = _meipass()

# PyInstaller's onedir layout puts the Qt runtime at:
#   <bundle>/_internal/PyQt6/Qt6/bin
#   <bundle>/_internal/PyQt6/Qt6/plugins
#   <bundle>/_internal/PyQt6/Qt6/plugins/platforms
qt_bin = os.path.join(bundle, "PyQt6", "Qt6", "bin")
qt_plugins = os.path.join(bundle, "PyQt6", "Qt6", "plugins")
qt_platforms = os.path.join(qt_plugins, "platforms")

# Prepend Qt's bin directory to PATH so its DLLs resolve via the standard
# loader search order when PyQt6.QtCore etc. are imported.
if os.path.isdir(qt_bin):
    os.environ["PATH"] = qt_bin + os.pathsep + os.environ.get("PATH", "")

# Tell Qt where to find its plugins (and especially the windows platform
# plugin). Setting both names is harmless and covers Qt 5/6 differences.
if os.path.isdir(qt_plugins):
    os.environ["QT_PLUGIN_PATH"] = qt_plugins
if os.path.isdir(qt_platforms):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_platforms
