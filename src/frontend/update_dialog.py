from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src import __version__
from src.frontend.theme import get_theme, normalize_theme_id, refresh_glass_shells


class UpdateInfoDialog(QDialog):
    def __init__(self, latest_version: str, changelog: str, download_url: str, parent=None):
        super().__init__(parent)
        self.latest_version = latest_version
        self.changelog = changelog
        self.download_url = download_url
        self._drag_pos = None
        self.frame = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Update Available")
        self.resize(420, 480)
        self.setMinimumSize(320, 360)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.frame = QFrame(self)
        self.frame.setObjectName("glassPanel")
        self.frame.setGeometry(0, 0, 420, 480)

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel(f"Update Available — Nudge v{self.latest_version}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        current = QLabel(f"Current version: {__version__}")
        current.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cfont = current.font()
        cfont.setPointSize(12)
        current.setFont(cfont)
        layout.addWidget(current)

        changelog_label = QLabel("What's new:")
        clfont = changelog_label.font()
        clfont.setPointSize(14)
        clfont.setBold(True)
        changelog_label.setFont(clfont)
        layout.addWidget(changelog_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.changelog_edit = QTextEdit()
        self.changelog_edit.setReadOnly(True)
        self.changelog_edit.setPlainText(self.changelog if self.changelog else "(No changelog available)")
        scroll.setWidget(self.changelog_edit)
        layout.addWidget(scroll, stretch=1)

        note = QLabel("The app will restart after installing.")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nfont = note.font()
        nfont.setPointSize(10)
        note.setFont(nfont)
        layout.addWidget(note)

        btn_row = QHBoxLayout()
        later_btn = QPushButton("Remind Me Later")
        later_btn.setObjectName("primaryButton")
        later_btn.clicked.connect(self.reject)
        btn_row.addWidget(later_btn)

        install_btn = QPushButton("Download && Install")
        install_btn.setObjectName("primaryButton")
        ifont = install_btn.font()
        ifont.setBold(True)
        install_btn.setFont(ifont)
        install_btn.clicked.connect(self.accept)
        btn_row.addWidget(install_btn)

        layout.addLayout(btn_row)

        self._update_overlap_opacity()

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
