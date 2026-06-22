"""
History list row — double-click text to restore (Stage 9).
"""

from __future__ import annotations

from typing import Callable, Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from src.frontend.responsive_text import ResponsiveTextRowHelper, configure_wrapping_label


class HistoryEntryLabel(QLabel):
    """History text that restores the entry on double-click."""

    def __init__(self, text: str, on_click: Optional[Callable[[], None]] = None, parent=None):
        super().__init__(text, parent)
        self._on_click = on_click
        self.setObjectName("historyEntryLabel")
        configure_wrapping_label(self)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Double-click to restore to the task list")

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._on_click is not None:
            self._on_click()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class HistoryRowWidget(QWidget):
    def __init__(
        self,
        text: str,
        text_size: int = 14,
        on_restore: Optional[Callable[[], None]] = None,
        on_delete: Optional[Callable[[], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.on_delete = on_delete
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setToolTip("Double-click to restore")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.label = HistoryEntryLabel(text, on_click=on_restore)
        font = self.label.font()
        font.setPointSize(text_size)
        self.label.setFont(font)
        layout.addWidget(self.label, 1)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.delete_btn.clicked.connect(self._handle_delete)
        layout.addWidget(self.delete_btn, 0, Qt.AlignmentFlag.AlignTop)

        self._text_layout = ResponsiveTextRowHelper(self, self.label, [self.delete_btn])
        QTimer.singleShot(0, self.sync_text_layout)

    def _handle_delete(self):
        if self.on_delete:
            self.on_delete()

    def sync_text_layout(self):
        self._text_layout.sync_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_text_layout()
