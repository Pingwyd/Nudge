"""Cross-platform frameless window drag helper for Linux/Wayland compatibility."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QWidget


def start_window_drag(window: QWidget, event_pos: QPoint) -> None:
    """Initiate a system window drag.

    On Wayland (Linux), Qt's ``QWindow::startSystemMove()`` is the only reliable
    way to move a frameless window.  On other platforms it works as well but we
    keep the manual ``window.move()`` fallback for older Qt versions.
    """
    wh = window.windowHandle()
    if wh is not None and hasattr(wh, "startSystemMove"):
        wh.startSystemMove()
    else:
        # Manual drag fallback (used on Windows / X11)
        _manual_drag_data = getattr(window, "_nudge_drag_data", None)
        if _manual_drag_data is None:
            window._nudge_drag_data = {"offset": event_pos - window.frameGeometry().topLeft()}


def continue_window_drag(window: QWidget, global_pos: QPoint) -> None:
    """Continue a manual window drag (no-op if system drag is active)."""
    wh = window.windowHandle()
    if wh is not None and hasattr(wh, "startSystemMove"):
        return  # system handles it
    data = getattr(window, "_nudge_drag_data", None)
    if data and "offset" in data:
        window.move(global_pos - data["offset"])


def end_window_drag(window: QWidget) -> None:
    """Clean up manual drag state."""
    if hasattr(window, "_nudge_drag_data"):
        del window._nudge_drag_data
