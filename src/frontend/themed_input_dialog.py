"""Themed glass-panel input dialog replacing QInputDialog (Fix C1)."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.constants import (
    INPUT_DIALOG_SIZE,
    INPUT_DIALOG_MIN_SIZE,
    INPUT_DIALOG_MAIN_LAYOUT_MARGINS,
    INPUT_DIALOG_LAYOUT_SPACING,
    INPUT_FIELD_MIN_HEIGHT,
    INPUT_DIALOG_BTN_HEIGHT,
    INPUT_DIALOG_BTN_MIN_WIDTH,
    RADIUS_PANEL,
    FONT_SIZE_LABEL_MD,
    SPACING_MD,
)


class ThemedInputDialog(GlassPanelDialog):
    """A themed input dialog with a QLineEdit, inheriting GlassPanelDialog styling."""

    def __init__(self, parent=None, title: str = "", label: str = "", default_text: str = ""):
        super().__init__(parent, overlap_radius=RADIUS_PANEL, escape_action="reject")
        self.setWindowTitle(title)
        self.resize(*INPUT_DIALOG_SIZE)
        self.setMinimumSize(*INPUT_DIALOG_MIN_SIZE)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*INPUT_DIALOG_MAIN_LAYOUT_MARGINS)
        layout.setSpacing(INPUT_DIALOG_LAYOUT_SPACING)

        prompt = QLabel(label)
        prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = prompt.font()
        font.setPointSize(FONT_SIZE_LABEL_MD)
        prompt.setFont(font)
        layout.addWidget(prompt)

        self._input = QLineEdit()
        self._input.setText(default_text)
        self._input.setMinimumHeight(INPUT_FIELD_MIN_HEIGHT)
        layout.addWidget(self._input)

        layout.addSpacing(30)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING_MD)
        btn_row.addStretch(1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.setFixedHeight(INPUT_DIALOG_BTN_HEIGHT)
        cancel_btn.setMinimumWidth(INPUT_DIALOG_BTN_MIN_WIDTH)
        cancel_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primaryButton")
        ok_btn.setFixedHeight(INPUT_DIALOG_BTN_HEIGHT)
        ok_btn.setMinimumWidth(INPUT_DIALOG_BTN_MIN_WIDTH)
        ok_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)

        self._input.setFocus()
        self._input.selectAll()

    def get_text(self) -> str:
        return self._input.text()
