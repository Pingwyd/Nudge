# X1a — Platform Utility + Desktop Pin (OS Layer)

## Objective
Guard Windows-specific `ctypes.windll` calls in `desktop_pin.py` behind platform checks. Provide macOS no-op stubs.

## Changes

### Step 1 — Create `src/os_layer/platform_utils.py`

```python
"""Cross-platform helpers: detect OS, open files, manage startup."""

import os
import sys
import subprocess
from pathlib import Path


def is_windows() -> bool:
    return sys.platform == "win32"


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_linux() -> bool:
    return sys.platform == "linux"


def open_file_explorer(path: str | Path):
    """Open the file manager to the given directory. Cross-platform."""
    path = str(Path(path).resolve())
    if is_windows():
        os.startfile(path)
    elif is_macos():
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def open_url(url: str):
    """Open a URL in the default browser with platform fallback."""
    import webbrowser
    opened = webbrowser.open(url)
    if not opened:
        if is_windows():
            os.startfile(url)
        elif is_macos():
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])
```

### Step 2 — Patch `src/os_layer/desktop_pin.py`

Wrap the entire file in a platform guard:

```python
"""Pin/unpin window to desktop. Windows: uses Win32 API. macOS/Linux: no-op."""

import sys

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    HWND_BOTTOM = 1
    HWND_NOTOPMOST = -2
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOACTIVATE = 0x0010

    def pin_to_desktop(hwnd):
        user32 = ctypes.windll.user32
        user32.SetWindowPos(
            hwnd, HWND_BOTTOM, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
        )

    def unpin_from_desktop(hwnd):
        user32 = ctypes.windll.user32
        user32.SetWindowPos(
            hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
        )
else:
    def pin_to_desktop(hwnd):
        pass  # macOS/Linux: desktop pinning not supported

    def unpin_from_desktop(hwnd):
        pass
```

### Step 3 — Verify imports in `main_window.py`

The import at line 51 still works:
```python
from src.os_layer.desktop_pin import pin_to_desktop, unpin_from_desktop
```

No changes needed — both functions are always defined now.

## Verification
- On Windows: pin/unpin works as before
- On macOS: import succeeds, `pin_to_desktop(hwnd)` is a no-op, no crash
- `open_file_explorer("/tmp")` on macOS runs `open /tmp`
- `open_url("https://example.com")` works on all platforms