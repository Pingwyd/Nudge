"""PriorityIndicator widget for showing task priority."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel
from src.frontend.theme import get_theme, normalize_theme_id


class PriorityIndicator(QLabel):
    """Small flag icon indicating high priority."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()

    def set_priority(self, priority: str | None, theme_id: str = "dark"):
        """Set the priority to display."""
        if priority == "high":
            theme = get_theme(normalize_theme_id(theme_id))
            accent = theme["colors"].get("accent", "#F5A623")
            self.setText("\u26a1")  # Lightning bolt emoji
            self.setStyleSheet(
                f"color: {accent}; font-size: 12px; background: transparent; border: none;"
            )
            self.show()
        else:
            self.hide()
