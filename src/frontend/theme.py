"""
Liquid Glass design system (Stage 7).

All colors, radii, and component QSS are driven from THEME dictionaries so Stage 8
can add a light palette without hunting scattered stylesheet strings.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QWidget

# --- Dark theme tokens (Liquid Glass) -------------------------------------------------

DARK_THEME: Dict[str, Any] = {
    "id": "dark",
    "colors": {
        "text": "#ffffff",
        "text_muted": "rgba(255, 255, 255, 180)",
        "glass_start": "rgba(30, 30, 30, 160)",
        "glass_end": "rgba(10, 10, 10, 130)",
        "border": "rgba(255, 255, 255, 60)",
        "border_highlight": "rgba(255, 255, 255, 90)",
        "input_bg": "rgba(0, 0, 0, 40)",
        "menu_bg": "rgba(40, 40, 40, 220)",
        "menu_border": "rgba(255, 255, 255, 50)",
        "hover": "rgba(255, 255, 255, 40)",
        "hover_strong": "rgba(255, 255, 255, 45)",
        "chrome_hover": "rgba(255, 255, 255, 30)",
        "chrome_separator": "rgba(255, 255, 255, 25)",
        "tab_bg": "rgba(255, 255, 255, 20)",
        "tab_selected": "rgba(255, 255, 255, 45)",
        "group_header_bg": "rgba(255, 255, 255, 18)",
        "group_header_border": "rgba(255, 255, 255, 45)",
        "group_header_hover": "rgba(255, 255, 255, 32)",
        "accent_button_bg": "rgba(255, 255, 255, 25)",
        "checkbox_indicator": "rgba(0, 0, 0, 40)",
        "checkbox_checked": "rgba(255, 255, 255, 150)",
        "checkbox_border": "rgba(255, 255, 255, 100)",
        "danger_bg": "rgba(255, 50, 50, 40)",
        "danger_border": "rgba(255, 50, 50, 80)",
        "danger_hover": "rgba(255, 50, 50, 70)",
        "scrollbar": "rgba(255, 255, 255, 80)",
        "scrollbar_track": "rgba(255, 255, 255, 14)",
        "tooltip_bg": "rgba(30, 30, 30, 240)",
        "tooltip_border": "rgba(255, 255, 255, 70)",
        "separator": "rgba(255, 255, 255, 35)",
        "drop_indicator": "rgba(255, 255, 255, 220)",
        "glass_overlap_solid": "rgba(18, 18, 18, 255)",
    },
    "radii": {
        "window": 20,
        "panel": 20,
        "input": 10,
        "button": 8,
        "tab": 8,
        "checkbox": 4,
        "menu": 5,
        "small": 4,
    },
    "fonts": {
        "family": "",
        "size_input": 14,
    },
}

# --- Light theme tokens (frosted glass, lighter palette) ------------------------------

LIGHT_THEME: Dict[str, Any] = {
    "id": "light",
    "colors": {
        "text": "#121214",
        "text_muted": "rgba(18, 18, 20, 200)",
        "glass_start": "rgba(255, 255, 255, 238)",
        "glass_end": "rgba(236, 240, 248, 215)",
        "border": "rgba(0, 0, 0, 55)",
        "border_highlight": "rgba(255, 255, 255, 245)",
        "input_bg": "rgba(255, 255, 255, 210)",
        "menu_bg": "rgba(252, 252, 255, 248)",
        "menu_border": "rgba(0, 0, 0, 40)",
        "hover": "rgba(0, 0, 0, 12)",
        "hover_strong": "rgba(0, 0, 0, 18)",
        "chrome_hover": "rgba(0, 0, 0, 14)",
        "chrome_separator": "rgba(0, 0, 0, 20)",
        "chrome_icon": "#2c2c2e",
        "tab_bg": "rgba(255, 255, 255, 150)",
        "tab_selected": "rgba(255, 255, 255, 235)",
        "group_header_bg": "rgba(255, 255, 255, 190)",
        "group_header_border": "rgba(0, 0, 0, 40)",
        "group_header_hover": "rgba(255, 255, 255, 225)",
        "accent_button_bg": "rgba(255, 255, 255, 210)",
        "checkbox_indicator": "rgba(255, 255, 255, 190)",
        "checkbox_checked": "rgba(44, 44, 46, 200)",
        "checkbox_border": "rgba(0, 0, 0, 55)",
        "danger_bg": "rgba(255, 80, 80, 55)",
        "danger_border": "rgba(200, 40, 40, 90)",
        "danger_hover": "rgba(255, 80, 80, 90)",
        "scrollbar": "rgba(0, 0, 0, 45)",
        "scrollbar_track": "rgba(0, 0, 0, 10)",
        "tooltip_bg": "rgba(252, 252, 255, 250)",
        "tooltip_border": "rgba(0, 0, 0, 35)",
        "separator": "rgba(0, 0, 0, 40)",
        "drop_indicator": "rgba(44, 44, 46, 220)",
        "glass_overlap_solid": "rgba(248, 248, 250, 255)",
    },
    "radii": deepcopy(DARK_THEME["radii"]),
    "fonts": deepcopy(DARK_THEME["fonts"]),
}

THEME_BY_ID: Dict[str, Dict[str, Any]] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
}


def normalize_theme_id(theme_id: str | None) -> str:
    if theme_id in THEME_BY_ID:
        return theme_id
    return "dark"


def get_theme(theme_id: str = "dark") -> Dict[str, Any]:
    return deepcopy(THEME_BY_ID[normalize_theme_id(theme_id)])


def _c(theme: Dict[str, Any], key: str) -> str:
    return theme["colors"][key]


def _chrome_button_color(theme: Dict[str, Any]) -> str:
    return theme["colors"].get("chrome_icon", _c(theme, "text"))


def _r(theme: Dict[str, Any], key: str) -> int:
    return theme["radii"][key]


def glass_panel_stylesheet(theme: Dict[str, Any]) -> str:
    """Gradient glass panel used for main window, settings, and history shells."""
    return f"""
        QWidget#glassPanel {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 {_c(theme, "glass_start")},
                stop: 1 {_c(theme, "glass_end")}
            );
            border-radius: {_r(theme, "panel")}px;
            border: 1px solid {_c(theme, "border")};
            border-top: 1px solid {_c(theme, "border_highlight")};
            border-left: 1px solid {_c(theme, "border_highlight")};
        }}
    """


def transparent_surface_stylesheet() -> str:
    return """
        QWidget#transparentSurface {
            background: transparent;
            border: none;
        }
    """


def nested_panel_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QFrame#nestedPanel {{
            background-color: {_c(theme, "input_bg")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "small")}px;
        }}
    """


def label_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QLabel {{
            color: {_c(theme, "text")};
            background: transparent;
            border: none;
        }}
    """


def line_edit_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QLineEdit {{
            background-color: {_c(theme, "input_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "input")}px;
            padding: 8px;
            font-size: 14px;
            min-height: 32px;
        }}
        QLineEdit:focus {{
            border: 1px solid {_c(theme, "border_highlight")};
        }}
    """


def _combo_dropdown_arrow_svg(theme: Dict[str, Any]) -> str:
    """Downward-pointing chevron as a base64 data URI for the combo box indicator."""
    import base64
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 8">'
        '<path d="M1 1.5l5 5 5-5" fill="none" '
        'stroke="#ffffff" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"/></svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"image: url(data:image/svg+xml;base64,{encoded});"


def combo_box_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QComboBox {{
            background-color: {_c(theme, "input_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "input")}px;
            padding: 6px 8px;
            min-height: 28px;
            font-size: 14px;
        }}
        QComboBox:hover {{
            border: 1px solid {_c(theme, "border_highlight")};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            border: none;
            width: 26px;
            {_combo_dropdown_arrow_svg(theme)}
        }}
        QComboBox::drop-down:hover {{
            border-left: 1px solid {_c(theme, "border")};
        }}
        QComboBox QAbstractItemView {{
            background-color: {_c(theme, "menu_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "menu_border")};
            border-radius: {_r(theme, "input")}px;
            selection-background-color: {_c(theme, "hover")};
            selection-color: {_c(theme, "text")};
            outline: none;
            font-size: 14px;
            padding: 4px;
        }}
        QComboBox QAbstractItemView::item {{
            background-color: transparent;
            color: {_c(theme, "text")};
            border: none;
            padding: 6px 10px;
            border-radius: {_r(theme, "input")}px;
            min-height: 20px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {_c(theme, "hover")};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {_c(theme, "hover_strong")};
            color: {_c(theme, "text")};
        }}
    """


def checkbox_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QCheckBox {{
            color: {_c(theme, "text")};
            font-size: 14px;
            padding: 5px;
            background: transparent;
            border: none;
            min-height: 24px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: {_r(theme, "checkbox")}px;
            border: 1px solid {_c(theme, "checkbox_border")};
            background-color: {_c(theme, "checkbox_indicator")};
        }}
        QCheckBox::indicator:checked {{
            background-color: {_c(theme, "checkbox_checked")};
        }}
    """


def menu_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QMenu {{
            background-color: {_c(theme, "menu_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "menu_border")};
            border-radius: {_r(theme, "menu")}px;
            padding: 4px;
            font-size: 14px;
        }}
        QMenu::item {{
            padding: 6px 24px 6px 12px;
        }}
        QMenu::item:selected {{
            background-color: {_c(theme, "hover")};
        }}
        QMenu::separator {{
            height: 1px;
            background: {_c(theme, "menu_border")};
            margin: 4px 8px;
        }}
    """


def tab_widget_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QTabWidget::pane {{
            border: none;
            background: transparent;
        }}
        QTabBar::tab {{
            color: {_c(theme, "text")};
            background: {_c(theme, "tab_bg")};
            border: 1px solid {_c(theme, "menu_border")};
            border-bottom: none;
            padding: 7px 12px;
            margin-right: 4px;
            border-top-left-radius: {_r(theme, "tab")}px;
            border-top-right-radius: {_r(theme, "tab")}px;
            font-size: 14px;
            min-height: 30px;
        }}
        QTabBar::tab:selected {{
            background: {_c(theme, "tab_selected")};
        }}
    """


def slider_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QSlider::groove:horizontal {{
            height: 10px;
            background: {_c(theme, "input_bg")};
            border-radius: 5px;
        }}
        QSlider::handle:horizontal {{
            background: {_c(theme, "text")};
            border-radius: 7px;
            width: 18px;
            height: 18px;
            margin: -4px 0;
        }}
    """


def scroll_bar_stylesheet(theme: Dict[str, Any]) -> str:
    track = _c(theme, "scrollbar_track")
    handle = _c(theme, "scrollbar")
    hover = _c(theme, "hover")
    hover_strong = _c(theme, "hover_strong")
    return f"""
        QScrollBar:vertical {{
            background: {track};
            width: 10px;
            margin: 4px 2px 4px 0;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {handle};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {hover};
        }}
        QScrollBar::handle:vertical:pressed {{
            background: {hover_strong};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: {track};
            height: 10px;
            margin: 0 4px 2px 4px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: {handle};
            border-radius: 4px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {hover};
        }}
        QScrollBar::handle:horizontal:pressed {{
            background: {hover_strong};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """


def scroll_area_stylesheet() -> str:
    return """
        QScrollArea {
            background: transparent;
            border: none;
        }
    """


def tooltip_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QToolTip {{
            color: {_c(theme, "text")};
            background-color: {_c(theme, "tooltip_bg")};
            border: 1px solid {_c(theme, "tooltip_border")};
            border-radius: {_r(theme, "small")}px;
            padding: 6px 8px;
        }}
    """


def dialog_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QDialog {{
            background: transparent;
        }}
        QMessageBox {{
            background-color: {_c(theme, "menu_bg")};
            color: {_c(theme, "text")};
        }}
        QMessageBox QLabel {{
            color: {_c(theme, "text")};
        }}
        QPushButton {{
            background: {_c(theme, "accent_button_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "button")}px;
            padding: 6px 14px;
            font-size: 14px;
            min-height: 28px;
        }}
        QPushButton:hover {{
            background: {_c(theme, "hover_strong")};
        }}
    """


def key_sequence_edit_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QKeySequenceEdit {{
            background-color: {_c(theme, "input_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "input")}px;
            padding: 6px 8px;
            font-size: 14px;
            min-height: 28px;
        }}
        QKeySequenceEdit:hover {{
            border: 1px solid {_c(theme, "border_highlight")};
        }}
        QKeySequenceEdit:focus {{
            border: 2px solid {_c(theme, "accent_button_bg")};
            background-color: {_c(theme, "hover")};
            color: {_c(theme, "text")};
        }}
    """


def chrome_button_stylesheet(theme: Dict[str, Any]) -> str:
    chrome_color = _chrome_button_color(theme)
    hover = _c(theme, "chrome_hover")
    radius = _r(theme, "small")
    sep = _c(theme, "chrome_separator")
    return f"""
        QPushButton#chromeButton,
        QPushButton#historyChromeButton,
        QPushButton#chromeButtonClose {{
            background: transparent;
            color: {chrome_color};
            border: none;
            font-size: 14px;
            font-weight: 600;
            padding: 0px 1px;
            margin: 0px;
        }}
        QPushButton#chromeButton,
        QPushButton#historyChromeButton {{
            border-right: 1px solid {sep};
        }}
        QPushButton#historyChromeButton {{
            padding: 0px 3px 0px 1px;
        }}
        QPushButton#chromeButton:hover,
        QPushButton#historyChromeButton:hover,
        QPushButton#chromeButtonClose:hover {{
            background: {hover};
            border-radius: {radius}px;
        }}
    """


def ghost_button_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QPushButton#ghostButton {{
            background: transparent;
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "button")}px;
            font-size: 14px;
            padding: 8px 12px;
            min-height: 32px;
        }}
        QPushButton#ghostButton:hover {{
            background: {_c(theme, "chrome_hover")};
            border: 1px solid {_c(theme, "border_highlight")};
        }}
        QPushButton#ghostButton:pressed {{
            background: {_c(theme, "hover")};
        }}
    """


def accent_icon_button_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QPushButton#accentIconButton {{
            background: {_c(theme, "accent_button_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "button")}px;
            font-size: 20px;
            font-weight: bold;
            padding: 0px;
            min-height: 22px;
        }}
        QPushButton#accentIconButton:hover {{
            background: {_c(theme, "hover_strong")};
            border: 1px solid {_c(theme, "border_highlight")};
        }}
    """


def primary_button_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QPushButton#primaryButton {{
            background: {_c(theme, "accent_button_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "button")}px;
            padding: 8px 12px;
            font-size: 14px;
            min-height: 32px;
        }}
        QPushButton#primaryButton:hover {{
            background: {_c(theme, "hover_strong")};
            border: 1px solid {_c(theme, "border_highlight")};
        }}
        QPushButton#primaryButton:pressed {{
            background: {_c(theme, "hover")};
        }}
        QPushButton#primaryButton:focus {{
            border: 2px solid {_c(theme, "border_highlight")};
        }}
    """


def sidebar_button_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QPushButton#sidebarButton {{
            background: transparent;
            color: {_c(theme, "text")};
            border: 1px solid transparent;
            border-radius: {_r(theme, "button")}px;
            padding: 6px 12px;
            font-size: 14px;
            min-height: 30px;
            min-width: 120px;
            text-align: left;
        }}
        QPushButton#sidebarButton:hover {{
            background: {_c(theme, "hover")};
            border: 1px solid {_c(theme, "border")};
        }}
        QPushButton#sidebarButton:checked {{
            background: {_c(theme, "accent_button_bg")};
            border: 1px solid {_c(theme, "border_highlight")};
            font-weight: bold;
        }}
    """


def danger_button_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QPushButton#dangerButton {{
            background-color: {_c(theme, "danger_bg")};
            color: {_c(theme, "text")};
            border-radius: {_r(theme, "button")}px;
            padding: 6px 10px;
            border: 1px solid {_c(theme, "danger_border")};
            font-size: 14px;
            min-height: 28px;
        }}
        QPushButton#dangerButton:hover {{
            background-color: {_c(theme, "danger_hover")};
        }}
    """


def history_entry_label_stylesheet(theme: Dict[str, Any]) -> str:
    """Clickable history row text (Stage 9 hover affordance)."""
    return f"""
        QLabel#historyEntryLabel {{
            color: {_c(theme, "text")};
            background: transparent;
            font-size: 14px;
            border: none;
            border-radius: {_r(theme, "small")}px;
            padding: 2px 4px;
        }}
        QLabel#historyEntryLabel:hover {{
            background: {_c(theme, "hover")};
            text-decoration: underline;
        }}
    """


def group_header_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QPushButton#groupHeader {{
            background: {_c(theme, "group_header_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "group_header_border")};
            border-radius: {_r(theme, "input")}px;
            padding: 8px 10px;
            text-align: left;
            font-size: 14px;
        }}
        QPushButton#groupHeader:hover {{
            background: {_c(theme, "group_header_hover")};
        }}
    """


def separator_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QFrame#hSeparator,
        QFrame#vSeparator {{
            background: {_c(theme, "separator")};
            border: none;
        }}
        QFrame#hSeparator {{
            max-height: 1px;
        }}
        QFrame#vSeparator {{
            max-width: 1px;
        }}
    """


def drop_indicator_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QFrame#dropIndicator {{
            background: {_c(theme, "drop_indicator")};
            border: none;
            border-radius: 1px;
        }}
    """


def glass_overlap_stylesheet(theme: Dict[str, Any], radius: int = 20) -> str:
    """Solid glass-panel background used when a frameless dialog overlaps the main window."""
    return f"""
        QWidget#glassPanel {{
            background: {_c(theme, "glass_overlap_solid")};
            border-radius: {radius}px;
            border: 1px solid {_c(theme, "border")};
        }}
    """


def build_application_stylesheet(theme: Dict[str, Any] | None = None) -> str:
    """Full app QSS generated from the theme dictionary."""
    theme = theme or DARK_THEME
    sections = [
        glass_panel_stylesheet(theme),
        transparent_surface_stylesheet(),
        nested_panel_stylesheet(theme),
        label_stylesheet(theme),
        line_edit_stylesheet(theme),
        combo_box_stylesheet(theme),
        checkbox_stylesheet(theme),
        menu_stylesheet(theme),
        tab_widget_stylesheet(theme),
        slider_stylesheet(theme),
        scroll_bar_stylesheet(theme),
        scroll_area_stylesheet(),
        tooltip_stylesheet(theme),
        dialog_stylesheet(theme),
        key_sequence_edit_stylesheet(theme),
        chrome_button_stylesheet(theme),
        ghost_button_stylesheet(theme),
        accent_icon_button_stylesheet(theme),
        primary_button_stylesheet(theme),
        sidebar_button_stylesheet(theme),
        danger_button_stylesheet(theme),
        group_header_stylesheet(theme),
        separator_stylesheet(theme),
        drop_indicator_stylesheet(theme),
        history_entry_label_stylesheet(theme),
    ]
    return "\n".join(sections)


def apply_theme_to_app(
    app,
    theme: Dict[str, Any] | str | None = None,
) -> Dict[str, Any]:
    """Apply generated QSS to the QApplication instance."""
    if isinstance(theme, str):
        resolved = get_theme(theme)
    else:
        resolved = deepcopy(theme or DARK_THEME)
    app.setStyleSheet(build_application_stylesheet(resolved))
    return resolved


def refresh_glass_shells(
    root: QWidget,
    theme: Dict[str, Any] | str | None = None,
) -> None:
    """
    Re-apply the glass panel gradient on dialog shells after a global theme change (H7).

    Frameless translucent dialogs may not repaint the outer shell from app QSS alone.
    """
    if isinstance(theme, str):
        resolved = get_theme(theme)
    else:
        resolved = deepcopy(theme or DARK_THEME)

    panel_css = glass_panel_stylesheet(resolved)
    nested_css = nested_panel_stylesheet(resolved)
    for frame in root.findChildren(QFrame):
        if frame.objectName() == "glassPanel":
            frame.setStyleSheet(panel_css)
        elif frame.objectName() == "nestedPanel":
            frame.setStyleSheet(nested_css)

    style = root.style()
    if style is None:
        root.update()
        return

    all_widgets = [root] + root.findChildren(QWidget, options=Qt.FindChildOption.FindChildrenRecursively)
    for widget in all_widgets:
        style.unpolish(widget)
        style.polish(widget)
        widget.update()
    root.update()
