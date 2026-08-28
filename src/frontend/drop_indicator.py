"""DropIndicatorOverlay — visual overlay shown during external drag-and-drop."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtWidgets import QWidget

from PyQt6.QtGui import QPainter
from src.frontend.theme import get_theme, normalize_theme_id


class DropIndicatorOverlay(QWidget):
    """Transparent overlay with a dashed border that signals 'drop here'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()
        self._theme_id = "dark"

    def show_overlay(self, theme_id: str | None = None) -> None:
        if theme_id is not None:
            self._theme_id = normalize_theme_id(theme_id)
        self.show()
        self.update()

    def hide_overlay(self) -> None:
        self.hide()

    def update_theme(self, theme_id: str) -> None:
        self._theme_id = normalize_theme_id(theme_id)
        if self.isVisible():
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        theme = get_theme(self._theme_id)
        c = theme["colors"]
        accent = c.get("accent", "#4fc3f7")
        border_color = QColor(accent)
        border_color.setAlpha(90)
        bg_color = QColor(accent)
        bg_color.setAlpha(12)

        # Fill with subtle tint
        painter.fillRect(self.rect(), bg_color)

        # Draw dashed border inset by 2px
        pen = QPen(border_color, 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(rect, 8, 8)
