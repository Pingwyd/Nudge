"""
History list row — double-click text to restore (Stage 9).
"""

from __future__ import annotations

from typing import Callable, Optional

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from src.frontend.responsive_text import ResponsiveTextRowHelper, configure_wrapping_label
from src.frontend.theme import (
    generate_svg_icon,
    get_theme,
    normalize_theme_id,
    svg_to_pixmap,
)
from src.constants import (
    HISTORY_CARD_MARGIN_LEFT,
    HISTORY_CARD_MARGIN_RIGHT,
    HISTORY_CARD_MARGIN_TOP,
    HISTORY_CARD_MARGIN_BOTTOM,
    HISTORY_CARD_INNER_SPACING,
    HISTORY_TEXT_META_SPACING,
)


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
        group_name: str = "",
        time_str: str = "",
        text_size: int = 14,
        on_restore: Optional[Callable[[], None]] = None,
        on_delete: Optional[Callable[[], None]] = None,
        theme_id: str = "dark",
        parent=None,
    ):
        super().__init__(parent)
        self.on_delete = on_delete
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setToolTip("Double-click to restore")

        self._apply_theme_colors(theme_id)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(HISTORY_CARD_MARGIN_LEFT, HISTORY_CARD_MARGIN_TOP, HISTORY_CARD_MARGIN_RIGHT, HISTORY_CARD_MARGIN_BOTTOM)
        layout.setSpacing(HISTORY_CARD_INNER_SPACING)

        check_icon = QLabel()
        check_icon.setFixedSize(18, 18)
        check_pixmap = svg_to_pixmap(
            generate_svg_icon("check", self._check_color, 18), 18
        )
        check_icon.setPixmap(check_pixmap)
        check_icon.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(check_icon, 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(HISTORY_TEXT_META_SPACING)
        text_col.setContentsMargins(0, 0, 0, 0)

        self.label = HistoryEntryLabel(text, on_click=on_restore)
        font = self.label.font()
        font.setPixelSize(text_size)
        self.label.setFont(font)
        text_col.addWidget(self.label)

        meta_parts = []
        if group_name:
            meta_parts.append(group_name)
        if time_str:
            meta_parts.append(time_str)
        if meta_parts:
            meta_label = QLabel(" \u00b7 ".join(meta_parts))
            meta_label.setStyleSheet(f"color: {self._tmc}; font-size: 11px; background: transparent; border: none;")
            text_col.addWidget(meta_label)

        layout.addLayout(text_col, 1)

        self.delete_btn = QPushButton()
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setToolTip("Delete from history")
        trash_color = self._danger_text
        trash_pixmap = svg_to_pixmap(generate_svg_icon("trash", trash_color, 16), 16)
        self.delete_btn.setIcon(QIcon(trash_pixmap))
        self.delete_btn.setIconSize(QSize(16, 16))
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {self._danger_border};
                border-radius: 8px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {self._danger_bg};
                border: 1px solid {self._danger_text};
            }}
            QPushButton:pressed {{
                background: {self._danger_hover};
            }}
        """)
        self.delete_btn.clicked.connect(self._handle_delete)
        layout.addWidget(self.delete_btn, 0, Qt.AlignmentFlag.AlignTop)

        self._text_layout = ResponsiveTextRowHelper(self, self.label, [self.delete_btn])
        QTimer.singleShot(0, self.sync_text_layout)

    def _apply_theme_colors(self, theme_id="dark"):
        theme = get_theme(theme_id)
        c = theme["colors"]
        self._tc = c.get("text", "#ffffff")
        self._tmc = c.get("text_muted", "rgba(255,255,255,180)")
        self._check_color = c.get("accent", "#4fc3f7")
        self._danger_text = c.get("danger_text", "#ff5555")
        self._danger_bg = c.get("danger_bg", "rgba(255,50,50,40)")
        self._danger_hover = c.get("danger_hover", "rgba(255,50,50,70)")
        self._danger_border = c.get("danger_border", "rgba(255,50,50,80)")

    def _handle_delete(self):
        if self.on_delete:
            self.on_delete()

    def sync_text_layout(self):
        self._text_layout.sync_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_text_layout()
