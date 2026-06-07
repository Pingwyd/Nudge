from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QFrame, QLabel, QPushButton, QVBoxLayout
from src.frontend.theme import get_theme, normalize_theme_id, refresh_glass_shells
from src import __app_name__, __version__


class SupportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None
        self.frame = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle(f"Support {__app_name__}")
        self.resize(340, 260)
        self.setMinimumSize(280, 220)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.frame = QFrame(self)
        self.frame.setObjectName("glassPanel")
        self.frame.setGeometry(0, 0, 340, 260)

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel(f"\u2764\ufe0f Support {__app_name__}")
        font = title.font()
        font.setPointSize(18)
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
        donate_btn.setMinimumHeight(40)
        donate_btn.clicked.connect(self._open_donate_link)
        layout.addWidget(donate_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self._update_overlap_opacity()

    def _open_donate_link(self):
        QDesktopServices.openUrl(QUrl("https://flutterwave.com/pay/nudge"))

    def _update_overlap_opacity(self):
        parent = self.parent()
        if parent is None:
            return
        theme_id = normalize_theme_id(getattr(parent, "app_state", {}).get("theme", "dark"))
        theme = get_theme(theme_id)
        overlap = self.frameGeometry().intersects(parent.frameGeometry()) if hasattr(parent, "frameGeometry") else False
        if overlap:
            solid = "rgba(248, 248, 250, 255)" if theme_id == "light" else "rgba(18, 18, 18, 255)"
            self.frame.setStyleSheet(f"""
                QWidget#glassPanel {{
                    background: {solid};
                    border-radius: 20px;
                    border: 1px solid {theme["colors"].get("border", "rgba(255,255,255,60)")};
                }}
            """)
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

    def resizeEvent(self, event):
        if self.frame is not None:
            self.frame.setGeometry(self.rect())
        super().resizeEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self._update_overlap_opacity()
