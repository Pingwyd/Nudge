from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src import __app_name__, __version__
from src.constants import (
    SUPPORT_DIALOG_DEFAULT,
    SUPPORT_DIALOG_MIN,
    MARGIN_STANDARD,
    SUPPORT_LAYOUT_SPACING,
    SUPPORT_TITLE_FONT_SIZE,
    SUPPORT_DONATE_BTN_MIN_HEIGHT,
)


class SupportDialog(GlassPanelDialog):
    def __init__(self, parent=None):
        super().__init__(parent, escape_action="reject")
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle(f"Support {__app_name__}")
        self.resize(*SUPPORT_DIALOG_DEFAULT)
        self.setMinimumSize(*SUPPORT_DIALOG_MIN)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*MARGIN_STANDARD)
        layout.setSpacing(SUPPORT_LAYOUT_SPACING)

        title = QLabel(f"\u2764\ufe0f Support {__app_name__}")
        font = title.font()
        font.setPointSize(SUPPORT_TITLE_FONT_SIZE)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(
            f"{__app_name__} v{__version__} is free and open-source.\n"
            "If you find it useful, consider buying me a coffee!"
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addStretch()

        donate_btn = QPushButton("\u2615 Buy Me a Coffee")
        donate_btn.setObjectName("primaryButton")
        donate_btn.setMinimumHeight(SUPPORT_DONATE_BTN_MIN_HEIGHT)
        donate_btn.clicked.connect(self._open_donate_link)
        layout.addWidget(donate_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._update_overlap_opacity()

    def _open_donate_link(self):
        QDesktopServices.openUrl(QUrl("https://flutterwave.com/pay/nudge"))
