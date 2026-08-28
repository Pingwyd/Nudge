"""TagPillWidget for displaying task tags as colored pills."""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget
from src.frontend.theme import get_theme, normalize_theme_id


# Predefined color palette for tags
TAG_COLORS = [
    "#90A4AE",  # Neutral gray
    "#81c784",  # Green
    "#FF6B5C",  # Coral (warning/overdue family)
    "#F5A623",  # Amber (feature / accent)
    "#ba68c8",  # Purple
    "#f06292",  # Pink
    "#4dd0e1",  # Teal
    "#e57373",  # Soft red
]

# Smart default colors for common tags
TAG_COLOR_DEFAULTS = {
    "work": "#4dd0e1",       # Teal
    "office": "#4dd0e1",
    "meeting": "#4dd0e1",
    "project": "#4dd0e1",
    "personal": "#81c784",   # Green
    "home": "#81c784",
    "health": "#81c784",
    "fitness": "#81c784",
    "urgent": "#FF6B5C",     # Coral
    "important": "#FF6B5C",
    "asap": "#FF6B5C",
    "overdue": "#FF6B5C",
    "feature": "#F5A623",    # Amber — feature-idea family
    "idea": "#F5A623",
    "enhancement": "#F5A623",
    "feature idea": "#F5A623",
    "errand": "#ba68c8",
    "shopping": "#ba68c8",
    "buy": "#ba68c8",
    "finance": "#ba68c8",
    "money": "#ba68c8",
    "budget": "#ba68c8",
    "creative": "#f06292",
    "art": "#f06292",
    "music": "#f06292",
    "learning": "#4dd0e1",
    "study": "#4dd0e1",
    "research": "#4dd0e1",
    "admin": "#90A4AE",
    "misc": "#90A4AE",
    "other": "#90A4AE",
    "bug": "#90A4AE",
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
        """Tinted pill: ~20% opacity fill + matching-hue text (legible on dark/light)."""
        color = self._color
        try:
            h = color.lstrip("#")
            if len(h) == 6:
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                bg = f"rgba({r}, {g}, {b}, 51)"  # ~20% of 255
            else:
                bg = color
                r = g = b = 200
        except ValueError:
            bg = color
            r = g = b = 200
        return f"""
            QLabel {{
                color: rgb({r}, {g}, {b});
                background: {bg};
                border-radius: 8px;
                font-size: 10px;
                padding: 1px 4px;
            }}
        """

    def set_color(self, color: str):
        """Update the pill color."""
        self._color = color
        self._label.setStyleSheet(self._get_stylesheet())

    def update_tag(self, tag_name: str, color: str = None):
        """Update tag name and optionally color, reusing the existing pill widget."""
        self._tag_name = tag_name
        if color is not None:
            self._color = color
        else:
            self._color = get_tag_color(tag_name)
        self._label.setText(tag_name)
        self._label.setStyleSheet(self._get_stylesheet())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.color_change_requested.emit(self._tag_name)
        super().mousePressEvent(event)
