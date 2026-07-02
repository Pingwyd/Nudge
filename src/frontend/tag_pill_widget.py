"""TagPillWidget for displaying task tags as colored pills."""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget
from src.frontend.theme import get_theme, normalize_theme_id


# Predefined color palette for tags
TAG_COLORS = [
    "#4fc3f7",  # Blue
    "#81c784",  # Green
    "#e57373",  # Red
    "#ffb74d",  # Orange
    "#ba68c8",  # Purple
    "#f06292",  # Pink
    "#4dd0e1",  # Teal
    "#90a4ae",  # Gray
]

# Smart default colors for common tags
TAG_COLOR_DEFAULTS = {
    "work": "#4fc3f7",       # Blue
    "office": "#4fc3f7",     # Blue
    "meeting": "#4fc3f7",    # Blue
    "project": "#4fc3f7",    # Blue
    "personal": "#81c784",   # Green
    "home": "#81c784",       # Green
    "health": "#81c784",     # Green
    "fitness": "#81c784",    # Green
    "urgent": "#e57373",     # Red
    "important": "#e57373",  # Red
    "asap": "#e57373",       # Red
    "errand": "#ffb74d",     # Orange
    "shopping": "#ffb74d",   # Orange
    "buy": "#ffb74d",        # Orange
    "finance": "#ba68c8",    # Purple
    "money": "#ba68c8",      # Purple
    "budget": "#ba68c8",     # Purple
    "creative": "#f06292",   # Pink
    "art": "#f06292",        # Pink
    "music": "#f06292",      # Pink
    "learning": "#4dd0e1",   # Teal
    "study": "#4dd0e1",      # Teal
    "research": "#4dd0e1",   # Teal
    "admin": "#90a4ae",      # Gray
    "misc": "#90a4ae",       # Gray
    "other": "#90a4ae",      # Gray
}


def get_tag_color(tag_name: str, custom_colors: dict = None) -> str:
    """Get color for a tag, using custom color if set, smart default, or palette hash."""
    if custom_colors and tag_name in custom_colors:
        return custom_colors[tag_name]
    # Check smart defaults for common tags (case-insensitive)
    lower = tag_name.lower().strip()
    if lower in TAG_COLOR_DEFAULTS:
        return TAG_COLOR_DEFAULTS[lower]
    # Deterministic color from palette based on tag name hash
    index = hash(tag_name) % len(TAG_COLORS)
    return TAG_COLORS[index]


class TagPillWidget(QWidget):
    """Small colored pill showing a tag name."""

    color_change_requested = pyqtSignal(str)  # Emits tag name

    def __init__(self, tag_name: str, color: str = None, parent=None):
        super().__init__(parent)
        self._tag_name = tag_name
        self._color = color or get_tag_color(tag_name)
        
        self.setFixedHeight(20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Click to change color for '{tag_name}'")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(0)
        
        self._label = QLabel(tag_name)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(self._get_stylesheet())
        layout.addWidget(self._label)

    def _get_stylesheet(self) -> str:
        """Generate stylesheet with current color."""
        return f"""
            QLabel {{
                color: white;
                background: {self._color};
                border-radius: 8px;
                font-size: 10px;
                padding: 1px 4px;
            }}
        """

    def set_color(self, color: str):
        """Update the pill color."""
        self._color = color
        self._label.setStyleSheet(self._get_stylesheet())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.color_change_requested.emit(self._tag_name)
        super().mousePressEvent(event)
