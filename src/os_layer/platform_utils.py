"""Cross-platform helpers: detect OS, open files, manage startup."""

from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path


def is_windows() -> bool:
    return sys.platform == "win32"


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def open_file_explorer(path: str | Path) -> None:
    """Open the file manager to the given directory. Cross-platform."""
    path = str(Path(path).resolve())
    if is_windows():
        os.startfile(path)
    elif is_macos():
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def open_url(url: str) -> bool:
    """Open a URL in the default browser with platform fallback."""
    opened = webbrowser.open(url)
    if not opened:
        if is_windows():
            os.startfile(url)
        elif is_macos():
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])
        opened = True
    return opened
