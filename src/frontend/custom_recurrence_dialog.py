"""Custom recurrence dialog for setting task recurrence intervals."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.theme import get_theme, normalize_theme_id
from src.constants import (
    REMINDER_OVERLAP_RADIUS,
    REMINDERS_LIST_MAIN_LAYOUT_MARGINS,
    RECURRENCE_DIALOG_SIZE,
    RECURRENCE_MAX_COUNT,
    RECURRENCE_MIN_COUNT,
    FONT_SIZE_BODY,
    SPACING_MD,
)

if TYPE_CHECKING:
    from src.frontend.dialog_context import DialogContext

logger = logging.getLogger(__name__)


class CustomRecurrenceDialog(GlassPanelDialog):
    """Dialog for setting a custom recurrence interval on a task."""

    def __init__(
        self,
        ctx: DialogContext,
        task_ref: dict,
        on_accept: Callable,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent, overlap_radius=REMINDER_OVERLAP_RADIUS, escape_action="reject")
        self._ctx = ctx
        self._task_ref = task_ref
        self._on_accept = on_accept
        self.setWindowTitle("Custom Recurrence")
        self.setFixedSize(*RECURRENCE_DIALOG_SIZE)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*REMINDERS_LIST_MAIN_LAYOUT_MARGINS)
        layout.setSpacing(SPACING_MD)

        title = QLabel("Set Custom Recurrence")
        title.setStyleSheet(f"font-weight: bold; font-size: {FONT_SIZE_BODY}px;")
        layout.addWidget(title)

        type_layout = QHBoxLayout()
        type_label = QLabel("Every:")
        type_layout.addWidget(type_label)
        type_combo = QComboBox()
        type_combo.addItems(["Days", "Weeks", "Months", "Years"])
        type_layout.addWidget(type_combo)
        layout.addLayout(type_layout)
        self._type_combo = type_combo

        count_layout = QHBoxLayout()
        count_label = QLabel("Interval:")
        count_layout.addWidget(count_label)
        count_spin = QSpinBox()
        count_spin.setRange(RECURRENCE_MIN_COUNT, RECURRENCE_MAX_COUNT)
        count_spin.setValue(RECURRENCE_MIN_COUNT)
        count_layout.addWidget(count_spin)
        layout.addLayout(count_layout)
        self._count_spin = count_spin

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        set_btn = QPushButton("Set")
        set_btn.setObjectName("primaryButton")
        set_btn.clicked.connect(self.accept)
        btn_layout.addWidget(set_btn)
        layout.addLayout(btn_layout)

    def accept(self) -> None:
        type_map = {0: "daily", 1: "weekly", 2: "monthly", 3: "yearly"}
        recurrence_type = type_map[self._type_combo.currentIndex()]
        interval = self._count_spin.value()
        self._on_accept(self._task_ref, recurrence_type, interval)
        super().accept()
