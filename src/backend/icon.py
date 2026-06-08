"""
Application icon loader.

Resolves ``icon.ico`` / ``icon.icns`` / ``icon.png`` whether the app is
running from source (project root) or from a PyInstaller bundle
(``sys._MEIPASS``), and exposes a single ``get_app_icon()`` factory
returning a cached ``QIcon``.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

from PyQt6.QtGui import QIcon

ICON_NAMES = ("icon.ico", "icon.icns", "icon.png")


def get_app_icon_path() -> Path | None:
    """Return the absolute path to the first found icon file (ico/icns/png)."""
    roots: list[Path] = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        roots.append(Path(sys._MEIPASS))
    roots.append(Path(__file__).resolve().parent.parent.parent)

    for root in roots:
        for name in ICON_NAMES:
            candidate = root / name
            try:
                if candidate.is_file():
                    return candidate
            except OSError:
                continue
    return None


@lru_cache(maxsize=1)
def get_app_icon() -> QIcon:
    """Return the application icon, cached after the first load.

    If the icon file is missing, an empty ``QIcon`` is returned — Qt
    tolerates this and just shows no icon (no crash, no warning).
    """
    path = get_app_icon_path()
    if path is None:
        return QIcon()
    return QIcon(os.fspath(path))
