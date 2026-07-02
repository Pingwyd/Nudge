"""Empathetic crash dialog with friendly error screen."""

from __future__ import annotations

import sys
from urllib.parse import quote

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QVBoxLayout)

from src import __version__
from src.backend.crash_reporter import build_mailto_body, write_crash_log
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.theme import (get_theme, normalize_theme_id,
                                refresh_glass_shells)
from src.os_layer.platform_utils import open_url
from src.constants import (
    CRASH_DIALOG_SIZE,
    CRASH_MAIN_LAYOUT_MARGINS,
    CRASH_LAYOUT_SPACING,
    CRASH_ICON_FONT_SIZE,
    CRASH_TITLE_FONT_SIZE,
    CRASH_ICON_HEIGHT,
    CRASH_DETAILS_TEXT_HEIGHT,
    CRASH_DETAIL_RESIZE_OFFSET,
    CRASH_COPIED_RESET_MS,
    RADIUS_PANEL,
    RADIUS_BUTTON,
    PROGRESS_BAR_RADIUS,
    DIALOG_BORDER_WIDTH,
    DIALOG_BTN_ALPHA,
    DIALOG_BTN_PAD_H,
    DIALOG_EDIT_ALPHA,
    DIALOG_EDIT_PAD,
    FONT_SIZE_LABEL_SM,
    FONT_SIZE_LABEL_MD,
)


class CrashDialog(GlassPanelDialog):
    """Empathetic crash dialog — friendly message with collapsible technical details."""

    def __init__(self, exc_type, exc_value, exc_tb, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nudge — Unexpected Error")
        self.setMinimumSize(*CRASH_DIALOG_SIZE)

        self._exc_type = exc_type
        self._exc_value = exc_value
        self._exc_tb = exc_tb
        self._error_info = build_mailto_body(exc_type, exc_value, exc_tb).replace("%0A", "\n").replace("%0D", "")
        # Decode URL-encoded characters for readable display
        from urllib.parse import unquote
        self._error_info = unquote(self._error_info)

        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*CRASH_MAIN_LAYOUT_MARGINS)
        layout.setSpacing(CRASH_LAYOUT_SPACING)

        icon = QLabel("\U0001f614")
        icon.setStyleSheet(f"font-size: {CRASH_ICON_FONT_SIZE}px; border: none; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedHeight(CRASH_ICON_HEIGHT)
        layout.addWidget(icon)

        title = QLabel("Something went wrong")
        title.setStyleSheet(f"font-size: {CRASH_TITLE_FONT_SIZE}px; font-weight: bold; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        description = QLabel(
            "Nudge encountered an unexpected error and needs to close. "
            "Your tasks have been saved automatically."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setStyleSheet(f"color: gray; font-size: {FONT_SIZE_LABEL_MD}px; border: none;")
        layout.addWidget(description)

        self._details_toggle = QPushButton("\u25b6 Technical Details")
        self._details_toggle.setObjectName("ghostButton")
        self._details_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._details_toggle.clicked.connect(self._toggle_details)
        layout.addWidget(self._details_toggle)

        self._details_text = QTextEdit()
        self._details_text.setPlainText(self._error_info)
        self._details_text.setReadOnly(True)
        self._details_text.setFixedHeight(CRASH_DETAILS_TEXT_HEIGHT)
        self._details_text.setStyleSheet(f"font-family: Consolas, monospace; font-size: {FONT_SIZE_LABEL_SM}px;")
        self._details_text.hide()
        layout.addWidget(self._details_text)

        btn_layout = QHBoxLayout()

        self._restart_btn = QPushButton("Restart Nudge")
        self._restart_btn.setObjectName("primaryButton")
        self._restart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._restart_btn.clicked.connect(self._restart_app)
        btn_layout.addWidget(self._restart_btn)

        self._report_btn = QPushButton("Copy Report")
        self._report_btn.setObjectName("ghostButton")
        self._report_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._report_btn.clicked.connect(self._copy_report)
        btn_layout.addWidget(self._report_btn)

        send_btn = QPushButton("Send Report")
        send_btn.setObjectName("ghostButton")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._send_report)
        btn_layout.addWidget(send_btn)

        layout.addLayout(btn_layout)

    def _toggle_details(self):
        if self._details_text.isVisible():
            self._details_text.hide()
            self._details_toggle.setText("\u25b6 Technical Details")
            self.resize(self.width(), self.height() - CRASH_DETAIL_RESIZE_OFFSET)
        else:
            self._details_text.show()
            self._details_toggle.setText("\u25c0 Technical Details")
            self.resize(self.width(), self.height() + CRASH_DETAIL_RESIZE_OFFSET)

    def _restart_app(self):
        import subprocess
        subprocess.Popen([sys.executable] + sys.argv)
        QApplication.quit()

    def _copy_report(self):
        QGuiApplication.clipboard().setText(self._error_info)
        self._report_btn.setText("Copied!")
        QTimer.singleShot(CRASH_COPIED_RESET_MS, lambda: self._report_btn.setText("Copy Report"))

    def _send_report(self):
        subject = f"Crash Report Nudge v{__version__}"
        body_text = self._error_info
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
        c = theme["colors"]
        self.bg_frame.setStyleSheet(f"""
            QWidget#glassPanel {{
                background: {c.get('menu_bg', 'rgba(30,30,30,240)')};
                border-radius: {RADIUS_PANEL}px;
                border: {DIALOG_BORDER_WIDTH}px solid {c.get('border', 'rgba(255,255,255,60)')};
            }}
            QLabel {{
                color: {c.get('text', '#e0e0e0')};
            }}
            QPushButton {{
                background: rgba(255,255,255,{DIALOG_BTN_ALPHA});
                color: {c.get('text', '#e0e0e0')};
                border: {DIALOG_BORDER_WIDTH}px solid {c.get('border', 'rgba(255,255,255,60)')};
                border-radius: {RADIUS_BUTTON}px;
                padding: 8px {DIALOG_BTN_PAD_H}px;
                font-size: {FONT_SIZE_LABEL_MD}px;
            }}
            QPushButton:hover {{
                background: {c.get('hover', 'rgba(255,255,255,20)')};
            }}
            QPushButton#primaryButton {{
                background: {c.get('accent', '#4fc3f7')};
                color: #000;
                border: none;
                font-weight: bold;
            }}
            QPushButton#primaryButton:hover {{
                background: {c.get('accent_hover', '#81d4fa')};
            }}
            QTextEdit {{
                background: rgba(0,0,0,{DIALOG_EDIT_ALPHA});
                color: {c.get('text', '#e0e0e0')};
                border: {DIALOG_BORDER_WIDTH}px solid {c.get('border', 'rgba(255,255,255,60)')};
                border-radius: {PROGRESS_BAR_RADIUS}px;
                padding: {DIALOG_EDIT_PAD}px;
            }}
        """)
        refresh_glass_shells(self, theme_id)


def install_crash_handler():
    """Replace sys.excepthook to show CrashDialog on unhandled exceptions."""
    old_hook = sys.excepthook

    def _handler(exc_type, exc_value, exc_tb):
        write_crash_log(exc_type, exc_value, exc_tb)
        try:
            app = QApplication.instance()
            if app is not None:
                dialog = CrashDialog(exc_type, exc_value, exc_tb)
                dialog.exec()
            else:
                old_hook(exc_type, exc_value, exc_tb)
        except Exception:
            old_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = _handler
