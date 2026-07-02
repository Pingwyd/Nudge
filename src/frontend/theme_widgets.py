"""Theme-related reusable widgets for the Settings dialog."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.frontend.theme import get_theme, normalize_theme_id
from src.frontend.utils import set_label_point_size
from src.constants import (
    THEME_CARD_SIZE,
    THEME_CARD_PREVIEW_HEIGHT,
    THEME_CARD_MARGINS,
    THEME_CARD_SPACING,
    THEME_CARD_PREVIEW_RADIUS,
    THEME_CARD_BORDER_WIDTH,
    SETTINGS_CARD_MARGINS,
    SETTINGS_CARD_CONTENT_SPACING,
    TOGGLE_SWITCH_SIZE,
    TOGGLE_SWITCH_RADIUS,
    TOGGLE_KNOB_DIAMETER,
    TOGGLE_KNOB_MARGIN,
    TOGGLE_SWITCH_ROW_SPACING,
    RADIUS_BUTTON,
    FONT_SIZE_BODY,
    FONT_SIZE_LABEL_SM,
    SPACING_SM,
    DIALOG_BORDER_WIDTH,
)


class ThemeCardWidget(QFrame):
    def __init__(self, theme_id, theme_name, colors, parent=None):
        super().__init__(parent)
        self.theme_id = theme_id
        self.theme_name = theme_name
        self.colors = colors
        self.setFixedSize(*THEME_CARD_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*THEME_CARD_MARGINS)
        layout.setSpacing(THEME_CARD_SPACING)

        preview = QFrame()
        bg = colors.get('glass_start', colors.get('input_bg', '#1e1e1e'))
        preview.setStyleSheet(f"background: {bg}; border: none; border-radius: {THEME_CARD_PREVIEW_RADIUS}px;")
        preview.setFixedHeight(THEME_CARD_PREVIEW_HEIGHT)
        layout.addWidget(preview)

        self._name_label = QLabel(theme_name)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._name_label)

        self._selected = False
        self._current_theme_id = "dark"
        self._update_style()

    def _update_style(self):
        from src.frontend.theme import get_theme, _c
        theme = get_theme(self._current_theme_id)
        text_color = _c(theme, "text")
        if self._selected:
            self.setStyleSheet(f"border: {THEME_CARD_BORDER_WIDTH}px solid #4fc3f7; border-radius: {RADIUS_BUTTON}px;")
        else:
            self.setStyleSheet(f"border: {THEME_CARD_BORDER_WIDTH}px solid transparent; border-radius: {RADIUS_BUTTON}px;")
        self._name_label.setStyleSheet(f"color: {text_color}; font-size: {FONT_SIZE_LABEL_SM}px; border: none;")

    def update_theme(self, theme_id):
        self._current_theme_id = theme_id
        self._update_style()

    def set_selected(self, selected):
        self._selected = selected
        self._update_style()


class SettingsCardWidget(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsCard")
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(f"font-weight: bold; font-size: {FONT_SIZE_BODY}px; border: none;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._current_theme_id = "dark"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*SETTINGS_CARD_MARGINS)
        layout.setSpacing(SPACING_SM)

        layout.addWidget(self._title_label)

        self._content = QWidget()
        self._content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(SETTINGS_CARD_CONTENT_SPACING)
        layout.addWidget(self._content)
        self._apply_card_style()

    def _apply_card_style(self):
        from src.frontend.theme import get_theme, _c
        theme = get_theme(self._current_theme_id)
        border_c = _c(theme, "border")
        glass_bg = _c(theme, "glass_start")
        self.setStyleSheet(
            f"#settingsCard {{ border: {DIALOG_BORDER_WIDTH}px solid {border_c}; border-radius: {RADIUS_BUTTON}px; background: {glass_bg}; }}"
        )
        title_color = _c(theme, "text")
        self._title_label.setStyleSheet(f"font-weight: bold; font-size: {FONT_SIZE_BODY}px; border: none; color: {title_color};")

    def update_theme(self, theme_id):
        self._current_theme_id = theme_id
        self._apply_card_style()

    def add_widget(self, widget):
        self._content_layout.addWidget(widget)


class ToggleSwitchWidget(QCheckBox):
    def __init__(self, on_color="#4fc3f7", off_color="#666666", parent=None):
        super().__init__(parent)
        self.setFixedSize(*TOGGLE_SWITCH_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._on_color = on_color
        self._off_color = off_color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.isChecked():
            painter.setBrush(QBrush(QColor(self._on_color)))
        else:
            painter.setBrush(QBrush(QColor(self._off_color)))
        painter.setPen(Qt.PenStyle.NoPen)
        w, h = TOGGLE_SWITCH_SIZE
        painter.drawRoundedRect(0, 0, w, h, TOGGLE_SWITCH_RADIUS, TOGGLE_SWITCH_RADIUS)
        painter.setBrush(QBrush(QColor("white")))
        knob_y = TOGGLE_KNOB_MARGIN
        if self.isChecked():
            knob_x = w - TOGGLE_KNOB_DIAMETER - TOGGLE_KNOB_MARGIN
        else:
            knob_x = TOGGLE_KNOB_MARGIN
        painter.drawEllipse(knob_x, knob_y, TOGGLE_KNOB_DIAMETER, TOGGLE_KNOB_DIAMETER)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self.isChecked())
            event.accept()

    def update_colors(self, on_color, off_color):
        self._on_color = on_color
        self._off_color = off_color
        self.update()


class ToggleSwitchRow(QWidget):
    def __init__(self, text, checked=False, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOGGLE_SWITCH_ROW_SPACING)
        self._label = QLabel(text)
        self._label.setWordWrap(True)
        self._label.setMinimumHeight(0)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        set_label_point_size(self._label, 12)
        layout.addWidget(self._label, 1)
        theme = get_theme(self._get_theme_id())
        c = theme["colors"]
        self._toggle = ToggleSwitchWidget(
            on_color=c.get("toggle_on", "#4fc3f7"),
            off_color=c.get("toggle_off", "#666666")
        )
        self._toggle.setChecked(checked)
        self._toggle.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self._toggle, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.toggled = self._toggle.toggled
        self.stateChanged = self._toggle.stateChanged

    def _get_theme_id(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "app_state"):
                return normalize_theme_id(parent.app_state.get("theme", "dark"))
            parent = parent.parent()
        return "dark"

    def isChecked(self):
        return self._toggle.isChecked()

    def setChecked(self, checked):
        self._toggle.setChecked(checked)

    def blockSignals(self, block):
        self._toggle.blockSignals(block)
