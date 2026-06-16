from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src import __app_name__, __version__


def _changelog_to_html(text: str) -> str:
    if not text:
        return "<p>No release notes available.</p>"
    lines = text.split("\n")
    html_parts = ['<div style="font-size:13px; line-height:1.6;">']
    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_parts.append("<br>")
        elif stripped.startswith("•") or stripped.startswith("-"):
            html_parts.append(f'<li style="margin:2px 0;">{stripped[1:].strip()}</li>')
        else:
            html_parts.append(f'<p style="margin:8px 0 4px 0; font-weight:bold;">{stripped}</p>')
    html_parts.append("</div>")
    return "".join(html_parts)


class WhatsNewDialog(GlassPanelDialog):
    def __init__(self, changelog: str, parent=None):
        super().__init__(parent, escape_action="accept")
        self.changelog = changelog
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle(f"What\u2019s New in {__app_name__}")
        self.resize(400, 380)
        self.setMinimumSize(320, 300)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel(f"What\u2019s New in {__app_name__} v{__version__}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        changelog_browser = QTextBrowser()
        changelog_browser.setOpenExternalLinks(False)
        changelog_browser.setHtml(_changelog_to_html(self.changelog or "Bug fixes and improvements."))
        changelog_browser.setStyleSheet("QTextBrowser { border: none; background: transparent; }")
        layout.addWidget(changelog_browser, stretch=1)

        btn_row = QHBoxLayout()
        got_it = QPushButton("Got it!")
        got_it.setObjectName("primaryButton")
        got_it.clicked.connect(self.accept)
        btn_row.addWidget(got_it)
        layout.addLayout(btn_row)

        self._update_overlap_opacity()
