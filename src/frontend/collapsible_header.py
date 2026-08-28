from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.frontend.theme import (
    generate_svg_icon,
    get_theme,
    normalize_theme_id,
    svg_to_pixmap,
)

_CHEVRON_SIZE = 14


class CollapsibleHeader(QWidget):
    def __init__(self, title, count, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._children = []
        self._title = title.upper()
        self._count = count
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 4)
        layout.setSpacing(4)

        self._chevron = QLabel()
        self._chevron.setFixedSize(_CHEVRON_SIZE, _CHEVRON_SIZE)
        self._chevron.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._chevron)

        self._label = QLabel(f"{self._title} \u00b7 {count}")
        self._label.setStyleSheet("font-weight: 600; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(self._label)
        layout.addStretch()

        self._apply_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle()

    def _apply_style(self):
        parent = self.parent()
        theme_id = "dark"
        if parent is not None:
            if hasattr(parent, '_get_theme_id'):
                theme_id = parent._get_theme_id()
            elif hasattr(parent, 'app_state'):
                theme_id = normalize_theme_id(parent.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        c = theme["colors"]
        tmc = c.get("text_muted", "rgba(255,255,255,180)")
        accent = c.get("accent", tmc)
        color = accent if self._expanded else tmc
        icon_key = "chevron_down" if self._expanded else "chevron_right"
        pix = svg_to_pixmap(generate_svg_icon(icon_key, color, _CHEVRON_SIZE), _CHEVRON_SIZE)
        self._chevron.setPixmap(pix)
        self._label.setStyleSheet(
            f"font-weight: 600; font-size: 12px; color: {tmc}; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )

    def _toggle(self):
        self._expanded = not self._expanded
        self._apply_style()
        alive = []
        for child in self._children:
            try:
                child.setVisible(self._expanded)
                alive.append(child)
            except RuntimeError:
                pass
        self._children = alive

    def add_child(self, widget):
        self._children.append(widget)

    def update_count(self, new_count: int):
        self._count = new_count
        self._label.setText(f"{self._title} \u00b7 {new_count}")
