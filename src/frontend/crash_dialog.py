"""Dialog shown on unhandled exception with Send Report and Copy buttons."""

from __future__ import annotations

import sys
from urllib.parse import quote

from src.os_layer.platform_utils import open_url

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src import __version__
from src.backend.crash_reporter import build_mailto_body, write_crash_log
from src.frontend.theme import (
    get_theme,
    normalize_theme_id,
    refresh_glass_shells,
)
from src.frontend.themed_message_dialog import ThemedMessageDialog


class CrashDialog(QDialog):
    """Report an unexpected error to the user and offer to send details."""

    def __init__(self, exc_type, exc_value, exc_tb, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nudge — Unexpected Error")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(500, 350)

        self._exc_type = exc_type
        self._exc_value = exc_value
        self._exc_tb = exc_tb
        self._drag_pos = None
        self.bg_frame = None

        self._build_ui()
        self._populate()
        self._apply_theme()

    def _build_ui(self):
        self.bg_frame = QFrame(self)
        self.bg_frame.setObjectName("glassPanel")
        self.bg_frame.setGeometry(0, 0, 500, 350)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        heading = QLabel(
            "<b>Something went wrong.</b><br>"
            "You can send a report to help fix the issue."
        )
        heading.setWordWrap(True)
        layout.addWidget(heading)

        self._details = QTextEdit()
        self._details.setReadOnly(True)
        self._details.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        layout.addWidget(self._details, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setObjectName("ghostButton")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_row.addWidget(copy_btn)

        send_btn = QPushButton("Send Report")
        send_btn.setObjectName("primaryButton")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._send_report)
        btn_row.addWidget(send_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("ghostButton")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _populate(self):
        body = build_mailto_body(self._exc_type, self._exc_value, self._exc_tb)
        self._details.setPlainText(body.replace("%0A", "\n").replace("%0D", ""))

    def _copy_to_clipboard(self):
        QGuiApplication.clipboard().setText(self._details.toPlainText())

    def _send_report(self):
        subject = f"Crash Report Nudge v{__version__}"
        body_text = self._details.toPlainText()
        QGuiApplication.clipboard().setText(body_text)
        gmail_uri = (
            f"https://mail.google.com/mail/u/0/?view=cm&fs=1"
            f"&to=nudgefeedback@gmail.com"
            f"&su={quote(subject)}"
            f"&body={quote(body_text)}"
        )
        open_url(gmail_uri)
        self.accept()

    def _apply_theme(self):
        parent = self.parent()
        theme_id = "dark"
        if parent and hasattr(parent, "app_state"):
            theme_id = normalize_theme_id(parent.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        refresh_glass_shells(self, theme_id)

    def resizeEvent(self, event):
        if self.bg_frame is not None:
            self.bg_frame.setGeometry(self.rect())
        super().resizeEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        parent = self.parent()
        if parent is None:
            return
        if isinstance(parent, QDialog):
            parent = parent.parent()
        if parent is None:
            return
        overlap = self.frameGeometry().intersects(parent.frameGeometry())
        theme_id = "dark"
        if hasattr(parent, "app_state"):
            theme_id = normalize_theme_id(parent.app_state.get("theme", "dark"))
        if overlap:
            from src.frontend.theme import glass_overlap_stylesheet
            theme = get_theme(theme_id)
            self.bg_frame.setStyleSheet(glass_overlap_stylesheet(theme, radius=20))
        else:
            refresh_glass_shells(self, theme_id)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()


def install_crash_handler():
    """Replace sys.excepthook to show CrashDialog on unhandled exceptions."""
    old_hook = sys.excepthook

    def _handler(exc_type, exc_value, exc_tb):
        write_crash_log(exc_type, exc_value, exc_tb)
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app is not None:
                dialog = CrashDialog(exc_type, exc_value, exc_tb)
                dialog.exec()
            else:
                old_hook(exc_type, exc_value, exc_tb)
        except Exception:
            old_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = _handler
