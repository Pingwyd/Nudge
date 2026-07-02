from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src import __app_name__, __version__
from src.constants import (
    WHATS_NEW_DIALOG_DEFAULT,
    WHATS_NEW_DIALOG_MIN,
    MARGIN_STANDARD,
    SPACING_LG,
    FONT_SIZE_BODY,
    FONT_SIZE_TITLE_LG,
    WHATS_NEW_LINE_HEIGHT,
    WHATS_NEW_LIST_ITEM_MARGIN,
    WHATS_NEW_LIST_PADDING,
    WHATS_NEW_HEADING_MARGIN_TOP,
    WHATS_NEW_HEADING_MARGIN_BOTTOM,
)


def _changelog_to_html(text: str) -> str:
    if not text:
        return "<p>No release notes available.</p>"
    lines = text.split("\n")
    html_parts = [f'<div style="font-size:{FONT_SIZE_BODY}px; line-height:{WHATS_NEW_LINE_HEIGHT};">']
    in_list = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append("<br>")
        elif stripped.startswith("\u2022") or stripped.startswith("-"):
            if not in_list:
                html_parts.append(f'<ul style="margin:{WHATS_NEW_LIST_ITEM_MARGIN}px 0; padding-left:{WHATS_NEW_LIST_PADDING}px;">')
                in_list = True
            html_parts.append(f'<li style="margin:{WHATS_NEW_LIST_ITEM_MARGIN}px 0;">{stripped[1:].strip()}</li>')
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f'<p style="margin:{WHATS_NEW_HEADING_MARGIN_TOP}px 0 {WHATS_NEW_HEADING_MARGIN_BOTTOM}px 0; font-weight:bold;">{stripped}</p>')
    if in_list:
        html_parts.append("</ul>")
    html_parts.append("</div>")
    return "".join(html_parts)


class WhatsNewDialog(GlassPanelDialog):
    def __init__(self, changelog: str, parent=None):
        super().__init__(parent, escape_action="accept")
        self.changelog = changelog
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle(f"What\u2019s New in {__app_name__}")
        self.resize(*WHATS_NEW_DIALOG_DEFAULT)
        self.setMinimumSize(*WHATS_NEW_DIALOG_MIN)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*MARGIN_STANDARD)
        layout.setSpacing(SPACING_LG)

        title = QLabel(f"What\u2019s New in {__app_name__} v{__version__}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(FONT_SIZE_TITLE_LG)
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
