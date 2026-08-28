"""Undo toast notification widget."""

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.frontend.theme import get_theme, normalize_theme_id
from src.constants import (
    TOAST_DEFAULT_TIMEOUT_MS,
    TOAST_MAX_WIDTH,
    TOAST_MARGINS,
    TOAST_EDGE_MARGIN,
    TOAST_RADIUS,
    FONT_SIZE_BODY,
    FONT_SIZE_LABEL_SM,
    SPACING_LG,
    DIALOG_BORDER_WIDTH,
)


class UndoToast(QFrame):
    """Non-blocking toast that auto-dismisses after a timeout, with an Undo button."""

    def __init__(
        self,
        parent,
        message,
        undo_callback,
        timeout_ms=TOAST_DEFAULT_TIMEOUT_MS,
        dismissed_callback=None,
        detail: str | None = None,
    ):
        super().__init__(parent)
        self._main_window = parent
        self._undo_callback = undo_callback
        self._dismissed_callback = dismissed_callback
        self.setObjectName("undoToast")
        self.setMaximumWidth(TOAST_MAX_WIDTH)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*TOAST_MARGINS)
        layout.setSpacing(SPACING_LG)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        msg_label = QLabel(message)
        msg_label.setObjectName("undoToastMessage")
        msg_label.setWordWrap(True)
        text_col.addWidget(msg_label)
        self._detail_label = None
        if detail:
            detail_label = QLabel(detail)
            detail_label.setObjectName("undoToastDetail")
            detail_label.setWordWrap(True)
            text_col.addWidget(detail_label)
            self._detail_label = detail_label
        layout.addLayout(text_col, 1)

        undo_btn = QPushButton("Undo")
        undo_btn.setObjectName("undoToastAction")
        undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        undo_btn.clicked.connect(self._on_undo)
        layout.addWidget(undo_btn)
        self._undo_btn = undo_btn

        dismiss_btn = QPushButton("X")
        dismiss_btn.setObjectName("ghostButton")
        dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        font = dismiss_btn.font()
        font.setBold(True)
        dismiss_btn.setFont(font)
        dismiss_btn.clicked.connect(self._dismiss)
        layout.addWidget(dismiss_btn)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(timeout_ms)
        self._timer.timeout.connect(self._dismiss)
        self._timer.start()

    def _install_focus_dismiss(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        def _on_focus_changed(old, new):
            if not self.isVisible():
                return
            if new is None:
                self._dismiss()
                return
            w = new
            while w is not None:
                if w is self or w is self._main_window:
                    return
                w = w.parent()
            self._dismiss()
        self._focus_conn = _on_focus_changed
        app.focusChanged.connect(_on_focus_changed)

    def _remove_focus_dismiss(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if hasattr(self, '_focus_conn'):
            try:
                app.focusChanged.disconnect(self._focus_conn)
            except RuntimeError:
                pass

    def _on_undo(self):
        if self._undo_callback:
            self._undo_callback()
        self._dismiss()

    def _dismiss(self):
        if self._timer.isActive():
            self._timer.stop()
        self._remove_focus_dismiss()
        self.hide()
        if self._dismissed_callback:
            self._dismissed_callback()
        self.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_theme()
        self._reposition()
        self._install_focus_dismiss()

    def _reposition(self):
        parent = self._main_window
        if parent is None:
            return
        self.adjustSize()
        if self.layout() is not None:
            self.layout().activate()
        tw = self.width()
        th = self.height()
        margin = TOAST_EDGE_MARGIN
        pw = parent.width()
        ph = parent.height()
        screen_pos = parent.mapToGlobal(QPoint(0, 0))
        screen = parent.screen().availableGeometry()
        x_right = screen_pos.x() + pw + margin
        if x_right + tw <= screen.right():
            x = x_right
        else:
            x = screen_pos.x() - tw - margin
        if x < screen.left():
            x = screen.left()
        y = screen_pos.y() + ph - th - margin
        if y < screen.top():
            y = screen.top()
        if y + th > screen.bottom():
            y = screen.bottom() - th
        self.move(x, y)

    def _apply_theme(self):
        parent = self._main_window
        theme_id = "dark"
        if parent and hasattr(parent, "app_state"):
            theme_id = normalize_theme_id(parent.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        c = theme["colors"]
        radii = theme["radii"]
        self.setStyleSheet(f"""
            QFrame#undoToast {{
                background: {c.get('glass_start', '#1e1e1e')};
                border: {DIALOG_BORDER_WIDTH}px solid {c.get('border', 'rgba(255,255,255,60)')};
                border-radius: {TOAST_RADIUS}px;
            }}
            QLabel#undoToastMessage {{
                color: {c.get('text', '#ffffff')};
                font-size: {FONT_SIZE_BODY}px;
                font-weight: 600;
            }}
            QLabel#undoToastDetail {{
                color: {c.get('text_muted', 'rgba(255,255,255,180)')};
                font-size: {FONT_SIZE_LABEL_SM}px;
            }}
            QPushButton#undoToastAction {{
                background: transparent;
                color: {c.get('accent', '#F5A623')};
                border: none;
                padding: 4px 8px;
                font-size: {FONT_SIZE_BODY}px;
                font-weight: 700;
            }}
            QPushButton#undoToastAction:hover {{
                color: {c.get('accent_hover', '#FFB83D')};
            }}
            QPushButton#ghostButton {{
                color: {c.get('text_muted', 'rgba(255,255,255,180)')};
                font-weight: bold;
                font-size: {FONT_SIZE_BODY}px;
                border: none;
                background: transparent;
            }}
        """)
