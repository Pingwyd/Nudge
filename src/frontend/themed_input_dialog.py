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
    FONT_SIZE_TITLE_MD,
    SPACING_MD,
)


class ThemedInputDialog(GlassPanelDialog):
    """A themed input dialog with a QLineEdit, inheriting GlassPanelDialog styling."""

    def __init__(
        self,
        parent=None,
        title: str = "",
        label: str = "",
        default_text: str = "",
        *,
        ok_label: str = "OK",
        placeholder: str | None = None,
    ):
        super().__init__(parent, overlap_radius=RADIUS_PANEL, escape_action="reject")
        self.setWindowTitle(title)
        self.resize(*INPUT_DIALOG_SIZE)
        self.setMinimumSize(*INPUT_DIALOG_MIN_SIZE)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*INPUT_DIALOG_MAIN_LAYOUT_MARGINS)
        layout.setSpacing(INPUT_DIALOG_LAYOUT_SPACING)

        if title:
            title_lbl = QLabel(title)
            title_lbl.setObjectName("dialogTitle")
            font = title_lbl.font()
            font.setPointSize(FONT_SIZE_TITLE_MD)
            font.setBold(True)
            title_lbl.setFont(font)
            layout.addWidget(title_lbl)

        if label and label != title:
            prompt = QLabel(label)
            prompt.setAlignment(Qt.AlignmentFlag.AlignLeft)
            font = prompt.font()
            font.setPointSize(FONT_SIZE_LABEL_MD)
            prompt.setFont(font)
            layout.addWidget(prompt)

        self._input = QLineEdit()
        self._input.setText(default_text)
        self._input.setMinimumHeight(INPUT_FIELD_MIN_HEIGHT)
        if placeholder:
            self._input.setPlaceholderText(placeholder)
        elif not default_text:
            self._input.setPlaceholderText(label or "Name")
        layout.addWidget(self._input)

        layout.addSpacing(12)

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

        ok_btn = QPushButton(ok_label)
        ok_btn.setObjectName("primaryButton")
        ok_btn.setFixedHeight(INPUT_DIALOG_BTN_HEIGHT)
        ok_btn.setMinimumWidth(max(INPUT_DIALOG_BTN_MIN_WIDTH, 64))
        ok_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)

        self._input.setFocus()
        self._input.selectAll()
        self._center_on_parent()

    def _center_on_parent(self) -> None:
        parent = self.parent()
        if parent is None:
            return
        self.adjustSize()
        pg = parent.frameGeometry()
        x = pg.x() + (pg.width() - self.width()) // 2
        y = pg.y() + (pg.height() - self.height()) // 2
        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        self._center_on_parent()

    def exec(self):
        parent = self.parent()
        overlay = getattr(parent, "_dim_overlay", None) if parent is not None else None
        if overlay is not None:
            overlay.show_dim()
        try:
            return super().exec()
        finally:
            if overlay is not None:
                overlay.hide_dim()

    def get_text(self) -> str:
        return self._input.text()
