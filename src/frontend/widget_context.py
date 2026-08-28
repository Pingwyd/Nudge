"""WidgetContext protocol — decouples child widgets from MainWindow."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from PyQt6.QtCore import QPoint
    from PyQt6.QtGui import QMimeData
    from PyQt6.QtWidgets import QWidget


@runtime_checkable
class WidgetContext(Protocol):
    """Minimal interface child widgets use instead of a MainWindow back-reference."""

    def get_theme_id(self) -> str:
        """Return the current normalized theme ID (e.g. 'dark', 'light', 'oled')."""
        ...

    def is_groups_enabled(self) -> bool:
        """Return True if group mode is active."""
        ...

    def get_tasks_widget(self) -> QWidget:
        """Return the scroll-area content widget (used for coordinate mapping in drag-drop)."""
        ...

    def get_tasks(self) -> list[dict]:
        """Return the current task list."""
        ...

    def save_tasks(self, tasks: list[dict]) -> None:
        """Persist the task list to disk."""
        ...

    def get_timer_for_task(self, task_id: str) -> object | None:
        """Return the TimerConfig for *task_id*, or None."""
        ...

    def update_group_drop_indicator(self, pos: QPoint) -> None:
        """Position the group-drop indicator at *pos* (global coordinates)."""
        ...

    def hide_group_drop_indicator(self) -> None:
        """Hide the group-drop indicator."""
        ...

    def on_group_drop(self, pos: QPoint, mime_data: QMimeData) -> None:
        """Handle a group-level drag-drop at *pos* with *mime_data*."""
        ...

    def on_row_dropped(self, source_id: str, target_group_id: str, insert_index: int) -> None:
        """Handle a task-row move: move *source_id* into *target_group_id* at *insert_index*."""
        ...
