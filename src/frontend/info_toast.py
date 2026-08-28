"""Simple info toast notification widget (no Undo button)."""

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from src.frontend.theme import get_theme, normalize_theme_id
from src.constants import (
    TOAST_DEFAULT_TIMEOUT_MS,
    TOAST_MAX_WIDTH,
    TOAST_MARGINS,
    TOAST_EDGE_MARGIN,
    TOAST_RADIUS,
    FONT_SIZE_BODY,
    SPACING_LG,
    DIALOG_BORDER_WIDTH,
)


class InfoToast(QFrame):
    """Non-blocking toast that auto-dismisses after a timeout."""

    def __init__(self, parent, message, timeout_ms=TOAST_DEFAULT_TIMEOUT_MS):
        super().__init__(parent)
        self._main_window = parent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setObjectName("infoToast")
        self.setMaximumWidth(TOAST_MAX_WIDTH)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*TOAST_MARGINS)
        layout.setSpacing(SPACING_LG)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

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

    def _dismiss(self):
        if self._timer.isActive():
            self._timer.stop()
        self.hide()
        self.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_theme()
        self._reposition()

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
        self.setStyleSheet(f"""
            QFrame#infoToast {{
                background: {c.get('glass_start', '#1e1e1e')};
                border: {DIALOG_BORDER_WIDTH}px solid {c.get('border', 'rgba(255,255,255,60)')};
                border-radius: {TOAST_RADIUS}px;
            }}
            QLabel {{
                color: {c.get('text', '#ffffff')};
                font-size: {FONT_SIZE_BODY}px;
            }}
            QPushButton {{
                color: {c.get('accent', '#4fc3f7')};
                font-weight: bold;
                font-size: {FONT_SIZE_BODY}px;
                border: none;
                background: transparent;
            }}
        """)
