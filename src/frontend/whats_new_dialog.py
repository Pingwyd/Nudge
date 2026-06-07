from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QTextEdit, QVBoxLayout
from src.frontend.theme import get_theme, normalize_theme_id, refresh_glass_shells
from src import __app_name__, __version__


class WhatsNewDialog(QDialog):
    def __init__(self, changelog: str, parent=None):
        super().__init__(parent)
        self.changelog = changelog
        self._drag_pos = None
        self.frame = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle(f"What\u2019s New in {__app_name__}")
        self.resize(400, 380)
        self.setMinimumSize(320, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.frame = QFrame(self)
        self.frame.setObjectName("glassPanel")
        self.frame.setGeometry(0, 0, 400, 380)

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel(f"What\u2019s New in {__app_name__} v{__version__}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        changelog_edit = QTextEdit()
        changelog_edit.setReadOnly(True)
        changelog_edit.setPlainText(self.changelog if self.changelog else "Bug fixes and improvements.")
        scroll.setWidget(changelog_edit)
        layout.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout()
        got_it = QPushButton("Got it!")
        got_it.setObjectName("primaryButton")
        got_it.clicked.connect(self.accept)
        btn_row.addWidget(got_it)
        layout.addLayout(btn_row)

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
