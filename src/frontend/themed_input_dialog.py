"""Themed glass-panel input dialog replacing QInputDialog (Fix C1)."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from src.frontend.glass_panel_dialog import GlassPanelDialog


class ThemedInputDialog(GlassPanelDialog):
    """A themed input dialog with a QLineEdit, inheriting GlassPanelDialog styling."""

    def __init__(self, parent=None, title: str = "", label: str = "", default_text: str = ""):
        super().__init__(parent, overlap_radius=20, escape_action="reject")
        self.setWindowTitle(title)
        self.resize(320, 160)
        self.setMinimumSize(260, 140)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        prompt = QLabel(label)
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = prompt.font()
        font.setPointSize(12)
        prompt.setFont(font)
        layout.addWidget(prompt)

        self._input = QLineEdit()
        self._input.setText(default_text)
        self._input.setMinimumHeight(30)
        layout.addWidget(self._input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primaryButton")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)

        self._input.setFocus()
        self._input.selectAll()

    def get_text(self) -> str:
        return self._input.text()
