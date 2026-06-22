"""
GlassPanelDialog — base class for all frameless glass-panel dialogs.

Encapsulates:
- FramelessWindowHint + WA_TranslucentBackground
- QFrame#glassPanel creation and resize sync
- Standard drag-to-move boilerplate
- Overlap-aware solid glass background (when dialog overlaps parent window)
- Configurable Escape key action
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QFrame, QDialog, QWidget

from src.frontend.theme import (
    get_theme,
    glass_overlap_stylesheet,
    normalize_theme_id,
    refresh_glass_shells,
)


class GlassPanelDialog(QDialog):
    """Base dialog with liquid-glass shell, drag support, and overlap detection."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        overlap_radius: int = 20,
        escape_action: str = "reject",
    ):
        """
        Parameters
        ----------
        parent : QWidget, optional
            Parent widget (typically MainWindow).
        overlap_radius : int
            Border radius for the solid overlap background.
        escape_action : str
            What Escape does: "reject", "accept", or "close".
        """
        super().__init__(parent)
        self._drag_pos = None
        self._drag_target = None
        self._drag_pending = False
        self._overlap_radius = overlap_radius
        self._escape_action = escape_action

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._apply_always_on_top()

        self.bg_frame = QFrame(self)
        self.bg_frame.setObjectName("glassPanel")

    # ── Theme resolution ─────────────────────────────────────────────

    def _get_theme_id(self) -> str:
        """Resolve the current theme id. Override if theme lives elsewhere."""
        parent = self.parent()
        if parent is None:
            return "dark"
        # Walk through QDialog grandparents to find a QMainWindow
        if isinstance(parent, QDialog):
            parent = parent.parent()
        if parent is None:
            return "dark"
        return normalize_theme_id(
            getattr(parent, "app_state", {}).get("theme", "dark")
        )

    def _apply_always_on_top(self):
        parent = self.parent()
        if parent is None:
            return
        if isinstance(parent, QDialog):
            parent = parent.parent()
        if parent is None:
            return
        if getattr(parent, "app_state", {}).get("alwaysOnTop", False):
            flags = self.windowFlags()
            flags |= Qt.WindowType.WindowStaysOnTopHint
            self.setWindowFlags(flags)

    # ── Overlap detection ────────────────────────────────────────────

    def _update_overlap_opacity(self) -> None:
        """Switch to solid glass background when this dialog overlaps its parent."""
        parent = self.parent()
        if parent is None:
            return
        if isinstance(parent, QDialog):
            parent = parent.parent()
        if parent is None:
            return
        overlap = self.frameGeometry().intersects(parent.frameGeometry())
        theme_id = self._get_theme_id()
        if overlap:
            theme = get_theme(theme_id)
            self.bg_frame.setStyleSheet(
                glass_overlap_stylesheet(theme, radius=self._overlap_radius)
            )
        else:
            refresh_glass_shells(self, theme_id)

    # ── Standard event handlers ──────────────────────────────────────

    def resizeEvent(self, event):
        self.bg_frame.setGeometry(self.rect())
        super().resizeEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self._update_overlap_opacity()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if (
            event.buttons() == Qt.MouseButton.LeftButton
            and self._drag_pos is not None
        ):
            self._drag_target = self.pos() + event.globalPosition().toPoint() - self._drag_pos
            self._drag_pos = event.globalPosition().toPoint()
            if not self._drag_pending:
                self._drag_pending = True
                QTimer.singleShot(0, self._apply_deferred_move)
            event.accept()

    def _apply_deferred_move(self):
        if self._drag_target is not None:
            self.move(self._drag_target)
            self._drag_target = None
        self._drag_pending = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self._escape_action == "reject":
                self.reject()
            elif self._escape_action == "accept":
                self.accept()
            elif self._escape_action == "close":
                self.close()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        event.accept()
        self.reject()
