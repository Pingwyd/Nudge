"""Themed glass-panel input dialog replacing QInputDialog (Fix C1)."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QLineEdit, QVBoxLayout

from src.frontend.dialog_layout import (
    add_dialog_footer,
    apply_dialog_content_layout,
    make_dialog_title,
)
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.constants import (
    DIALOG_INPUT_MIN_HEIGHT,
    FONT_SIZE_LABEL_MD,
    INPUT_DIALOG_MIN_SIZE,
    INPUT_DIALOG_SIZE,
    RADIUS_PANEL,
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
        apply_dialog_content_layout(layout)

        if title:
            layout.addWidget(make_dialog_title(title))

        if label and label != title:
            prompt = QLabel(label)
            prompt.setAlignment(Qt.AlignmentFlag.AlignLeft)
            font = prompt.font()
            font.setPixelSize(FONT_SIZE_LABEL_MD)
            prompt.setFont(font)
            layout.addWidget(prompt)

        self._input = QLineEdit()
        self._input.setText(default_text)
        self._input.setMinimumHeight(DIALOG_INPUT_MIN_HEIGHT)
        if placeholder:
            self._input.setPlaceholderText(placeholder)
        elif not default_text:
            self._input.setPlaceholderText(label or "Name")
        layout.addWidget(self._input)

        add_dialog_footer(
            layout,
            [
                ("Cancel", "ghost", self.reject),
                (ok_label, "primary", self.accept),
            ],
        )

        self._input.setFocus()
        self._input.selectAll()
        self.adjustSize()
        w = max(self.width(), INPUT_DIALOG_MIN_SIZE[0])
        h = max(self.height(), INPUT_DIALOG_MIN_SIZE[1])
        self.resize(w, h)
        self._center_on_parent()

    def _center_on_parent(self) -> None:
        parent = self.parent()
        if parent is None:
            return
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
