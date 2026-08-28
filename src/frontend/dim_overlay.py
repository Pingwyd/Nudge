"""Dim overlay confined to the main window while anchored dialogs are open."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget


class DimOverlay(QWidget):
    """Semi-transparent scrim covering the main window's content area."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("dimOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.hide()
        self._depth = 0

    def show_dim(self) -> None:
        self._depth += 1
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()

    def hide_dim(self) -> None:
        self._depth = max(0, self._depth - 1)
        if self._depth == 0:
            self.hide()

    def force_hide(self) -> None:
        self._depth = 0
        self.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent() is not None:
            self.setGeometry(self.parent().rect())

    def apply_theme(self, theme: dict) -> None:
        # Keep overlay dark enough to read on all themes
        self.setStyleSheet(
            "QWidget#dimOverlay { background: rgba(0, 0, 0, 140); border: none; }"
        )
