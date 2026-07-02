"""Shared context passed to extracted dialog classes."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass
class DialogContext:
    """Bundles the MainWindow attributes dialogs need, avoiding a direct back-reference."""
    app_state: dict
    state_manager: Any  # StateManager
    timer_manager: Any  # TimerManager
    screen: Any = None  # callable returning QScreen
    frame_geometry: Any = None  # callable returning QRect
    window_rects_to_avoid: Any = None  # callable returning list[QRect]
    place_dialog_avoiding_rects: Any = None  # callable(dialog, rects)
    task_row_widgets: dict = field(default_factory=dict)  # id(task_ref) -> widget
