"""Custom due date dialog for selecting task due dates."""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCalendarWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.theme import get_theme, normalize_theme_id
from src.constants import (
    DUE_DATE_DIALOG_SIZE,
    DUE_DATE_MAIN_LAYOUT_MARGINS,
    FONT_SIZE_BODY,
    REMINDER_OVERLAP_RADIUS,
    SPACING_MD,
)

if TYPE_CHECKING:
    from src.frontend.dialog_context import DialogContext

logger = logging.getLogger(__name__)


class CustomDueDateDialog(GlassPanelDialog):
    """Dialog for selecting a custom due date for a task."""

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
        self.setWindowTitle("Select Due Date")
        self.setFixedSize(*DUE_DATE_DIALOG_SIZE)
        self._build_ui()

    def _build_ui(self) -> None:
        theme_id = normalize_theme_id(self._ctx.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        c = theme["colors"]

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*DUE_DATE_MAIN_LAYOUT_MARGINS)
        layout.setSpacing(SPACING_MD)

        title = QLabel("Pick a due date")
        title.setStyleSheet(f"font-weight: bold; font-size: {FONT_SIZE_BODY}px;")
        layout.addWidget(title)

        calendar = QCalendarWidget()
        calendar.setStyleSheet(f"""
            QCalendarWidget {{
                background: transparent;
            }}
            QCalendarWidget QToolButton {{
                color: {c.get('text', '#e0e0e0')};
                background: transparent;
            }}
            QCalendarWidget QAbstractItemView {{
                color: {c.get('text', '#e0e0e0')};
                selection-background-color: {c.get('accent', '#4fc3f7')};
            }}
        """)
        layout.addWidget(calendar)
        self._calendar = calendar

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primaryButton")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def accept(self) -> None:
        selected = self._calendar.selectedDate().toString("yyyy-MM-dd")
        self._on_accept(self._task_ref, selected)
        super().accept()
