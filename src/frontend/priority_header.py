"""PriorityHeaderWidget — sticky header shown above high-priority tasks in flat list mode."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.constants import (
    PRIORITY_DIVIDER_HEIGHT,
    PRIORITY_HEADER_FONT_SIZE,
    PRIORITY_HEADER_HEIGHT,
    PRIORITY_HEADER_PADDING_H,
)
from src.frontend.theme import get_theme, normalize_theme_id


class PriorityHeaderWidget(QWidget):
    """Small uppercase label with accent background and bottom divider."""

    def __init__(self, theme_id: str = "dark", parent=None):
        super().__init__(parent)
        self.setFixedHeight(PRIORITY_HEADER_HEIGHT)
        self.setObjectName("priorityHeader")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(PRIORITY_HEADER_PADDING_H, 0, PRIORITY_HEADER_PADDING_H, 0)
        layout.setSpacing(4)

        self._icon_label = QLabel("\u26a1")  # ⚡
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon_label)

        self._text_label = QLabel("HIGH PRIORITY")
        layout.addWidget(self._text_label)

        layout.addStretch(1)

        self._apply_theme(theme_id)

    def _apply_theme(self, theme_id: str) -> None:
        theme = get_theme(normalize_theme_id(theme_id))
        c = theme["colors"]
        header_bg = c.get("priority_header_bg", "rgba(79, 195, 247, 25)")
        header_text = c.get("priority_header_text", "#4fc3f7")
        divider_color = c.get("priority_divider", "rgba(79, 195, 247, 60)")

        self.setStyleSheet(
            f"QWidget#priorityHeader {{ background: {header_bg}; border: none; }}"
        )
        self._icon_label.setStyleSheet(
            f"color: {header_text}; font-size: {PRIORITY_HEADER_FONT_SIZE}px; "
            f"background: transparent; border: none;"
        )
        self._text_label.setStyleSheet(
            f"color: {header_text}; font-size: {PRIORITY_HEADER_FONT_SIZE}px; "
            f"font-weight: 600; letter-spacing: 1px; "
            f"background: transparent; border: none;"
        )
        # Bottom border via a separate frame isn't needed — we paint via QSS.
        # Use a 1px bottom border on the widget itself.
        self.setStyleSheet(
            f"QWidget#priorityHeader {{ "
            f"background: {header_bg}; "
            f"border: none; "
            f"border-bottom: {PRIORITY_DIVIDER_HEIGHT}px solid {divider_color}; "
            f"}}"
        )

    def update_theme(self, theme_id: str) -> None:
        """Re-apply colors when the app theme changes."""
        self._apply_theme(theme_id)
