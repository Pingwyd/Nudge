"""
Liquid Glass design system (Stage 7).

All colors, radii, and component QSS are driven from THEME dictionaries so Stage 8
can add a light palette without hunting scattered stylesheet strings.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from PyQt6.QtCore import QObject, Qt, QEvent
from PyQt6.QtWidgets import QFrame, QWidget

# --- Dark theme tokens (Liquid Glass) -------------------------------------------------

DARK_THEME: Dict[str, Any] = {
    "id": "dark",
    "colors": {
        "text": "#ffffff",
        "text_muted": "rgba(255, 255, 255, 180)",
        "glass_start": "rgba(30, 30, 30, 220)",
        "glass_end": "rgba(10, 10, 10, 200)",
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
        "group_header_bg": "rgba(255, 255, 255, 28)",
        "group_header_border": "rgba(255, 255, 255, 55)",
        "group_header_hover": "rgba(255, 255, 255, 40)",
        "accent_button_bg": "rgba(245, 166, 35, 35)",
        "checkbox_indicator": "rgba(0, 0, 0, 40)",
        "checkbox_checked": "#F5A623",
        "checkbox_border": "rgba(255, 255, 255, 100)",
        "danger_bg": "rgba(255, 50, 50, 40)",
        "danger_border": "rgba(255, 50, 50, 80)",
        "danger_hover": "rgba(255, 50, 50, 70)",
        "danger_text": "#ff5555",
        "scrollbar": "rgba(255, 255, 255, 80)",
        "scrollbar_track": "rgba(255, 255, 255, 14)",
        "tooltip_bg": "rgba(30, 30, 30, 240)",
        "tooltip_border": "rgba(255, 255, 255, 70)",
        "separator": "rgba(255, 255, 255, 35)",
        "drop_indicator": "#F5A623",
        "glass_overlap_solid": "rgba(18, 18, 18, 255)",
        # Warm amber accent — meaning only (CTAs, focus, priority, active states)
        "accent": "#F5A623",
        "accent_hover": "#FFB83D",
        "accent_pressed": "#E09515",
        "on_accent": "#1A1205",
        "muted": "#666666",
        "toggle_on": "#F5A623",
        "toggle_off": "#666666",
        "input_focus_glow": "0 0 8px rgba(245, 166, 35, 0.28)",
        "dialog_shadow": "0 8px 32px rgba(0, 0, 0, 0.4)",
        "priority_header_bg": "rgba(245, 166, 35, 25)",
        "priority_header_text": "#F5A623",
        "priority_divider": "rgba(245, 166, 35, 60)",
        # Amber-tinted thick divider on last priority-block task
        "section_divider": "rgba(245, 166, 35, 90)",
        # Coral — due/overdue/warning (never share amber's role)
        "warning": "#FF6B5C",
        "overdue": "#FF6B5C",
        "due_soon": "#FF8A7A",
        "search_match_bg": "rgba(245, 166, 35, 45)",
        "tag_feature": "#F5A623",
        "tag_neutral": "#90A4AE",
        "icon": "#ffffff",
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
        "size_ui": 13,
        "size_title": 14,
        "weight_task": 500,
        "weight_header": 500,
    },
    "spacing": {
        "row_padding_v": 9,
        "row_padding_h_left": 12,
        "row_padding_h_right": 8,
        "checkbox_size": 20,
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
        "group_header_bg": "rgba(255, 255, 255, 220)",
        "group_header_border": "rgba(0, 0, 0, 48)",
        "group_header_hover": "rgba(255, 255, 255, 240)",
        "accent_button_bg": "rgba(201, 133, 10, 28)",
        "checkbox_indicator": "rgba(255, 255, 255, 190)",
        "checkbox_checked": "#C9850A",
        "checkbox_border": "rgba(0, 0, 0, 55)",
        "danger_bg": "rgba(255, 80, 80, 55)",
        "danger_border": "rgba(200, 40, 40, 90)",
        "danger_hover": "rgba(255, 80, 80, 90)",
        "danger_text": "#c82828",
        "scrollbar": "rgba(0, 0, 0, 45)",
        "scrollbar_track": "rgba(0, 0, 0, 10)",
        "tooltip_bg": "rgba(252, 252, 255, 250)",
        "tooltip_border": "rgba(0, 0, 0, 35)",
        "separator": "rgba(0, 0, 0, 40)",
        "drop_indicator": "#C9850A",
        "glass_overlap_solid": "rgba(248, 248, 250, 255)",
        "accent": "#C9850A",
        "accent_hover": "#D99412",
        "accent_pressed": "#A86F08",
        "on_accent": "#1A1205",
        "muted": "#8e8e93",
        "toggle_on": "#C9850A",
        "toggle_off": "#c7c7cc",
        "input_focus_glow": "0 0 6px rgba(201, 133, 10, 0.22)",
        "dialog_shadow": "0 4px 16px rgba(0, 0, 0, 0.15)",
        "priority_header_bg": "rgba(201, 133, 10, 22)",
        "priority_header_text": "#C9850A",
        "priority_divider": "rgba(201, 133, 10, 55)",
        "section_divider": "rgba(201, 133, 10, 85)",
        "warning": "#E85A4C",
        "overdue": "#E85A4C",
        "due_soon": "#F0786A",
        "search_match_bg": "rgba(201, 133, 10, 40)",
        "tag_feature": "#C9850A",
        "tag_neutral": "#8E8E93",
        "icon": "#2c2c2e",
    },
    "radii": deepcopy(DARK_THEME["radii"]),
    "fonts": deepcopy(DARK_THEME["fonts"]),
    "spacing": deepcopy(DARK_THEME["spacing"]),
}

# --- OLED theme tokens (pure black background for OLED displays) --------------------

OLED_THEME: Dict[str, Any] = {
    "id": "oled",
    "colors": {
        "text": "#ffffff",
        "text_muted": "rgba(255, 255, 255, 160)",
        "glass_start": "rgba(0, 0, 0, 255)",
        "glass_end": "rgba(0, 0, 0, 255)",
        "border": "rgba(255, 255, 255, 40)",
        "border_highlight": "rgba(255, 255, 255, 70)",
        "input_bg": "rgba(255, 255, 255, 20)",
        "menu_bg": "rgba(0, 0, 0, 255)",
        "menu_border": "rgba(255, 255, 255, 35)",
        "hover": "rgba(255, 255, 255, 25)",
        "hover_strong": "rgba(255, 255, 255, 35)",
        "chrome_hover": "rgba(255, 255, 255, 20)",
        "chrome_separator": "rgba(255, 255, 255, 18)",
        "tab_bg": "rgba(255, 255, 255, 12)",
        "tab_selected": "rgba(255, 255, 255, 30)",
        "group_header_bg": "rgba(255, 255, 255, 18)",
        "group_header_border": "rgba(255, 255, 255, 40)",
        "group_header_hover": "rgba(255, 255, 255, 28)",
        "accent_button_bg": "rgba(245, 166, 35, 28)",
        "checkbox_indicator": "rgba(255, 255, 255, 25)",
        "checkbox_checked": "#F5A623",
        "checkbox_border": "rgba(255, 255, 255, 80)",
        "danger_bg": "rgba(255, 40, 40, 35)",
        "danger_border": "rgba(255, 40, 40, 70)",
        "danger_hover": "rgba(255, 40, 40, 60)",
        "danger_text": "#ff4444",
        "scrollbar": "rgba(255, 255, 255, 60)",
        "scrollbar_track": "rgba(255, 255, 255, 8)",
        "tooltip_bg": "rgba(20, 20, 20, 245)",
        "tooltip_border": "rgba(255, 255, 255, 50)",
        "separator": "rgba(255, 255, 255, 25)",
        "drop_indicator": "#F5A623",
        "glass_overlap_solid": "rgba(0, 0, 0, 255)",
        "accent": "#F5A623",
        "accent_hover": "#FFB83D",
        "accent_pressed": "#E09515",
        "on_accent": "#1A1205",
        "muted": "#666666",
        "toggle_on": "#F5A623",
        "toggle_off": "#666666",
        "input_focus_glow": "0 0 8px rgba(245, 166, 35, 0.3)",
        "dialog_shadow": "0 8px 32px rgba(0, 0, 0, 0.6)",
        "priority_header_bg": "rgba(245, 166, 35, 20)",
        "priority_header_text": "#F5A623",
        "priority_divider": "rgba(245, 166, 35, 50)",
        "section_divider": "rgba(245, 166, 35, 85)",
        "warning": "#FF6B5C",
        "overdue": "#FF6B5C",
        "due_soon": "#FF8A7A",
        "search_match_bg": "rgba(245, 166, 35, 45)",
        "tag_feature": "#F5A623",
        "tag_neutral": "#90A4AE",
        "icon": "#ffffff",
    },
    "radii": deepcopy(DARK_THEME["radii"]),
    "fonts": deepcopy(DARK_THEME["fonts"]),
    "spacing": deepcopy(DARK_THEME["spacing"]),
}

THEME_BY_ID: Dict[str, Dict[str, Any]] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "oled": OLED_THEME,
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


def _icon_asset_path(icon_type: str) -> Path | None:
    """Resolve ``src/assets/icons/{icon_type}.svg`` (source or frozen)."""
    import sys
    from pathlib import Path

    roots: list[Path] = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        roots.append(Path(sys._MEIPASS) / "src" / "assets" / "icons")
        roots.append(Path(sys._MEIPASS) / "assets" / "icons")
    # theme.py → frontend → src → project; assets live under src/assets
    here = Path(__file__).resolve().parent  # src/frontend
    roots.append(here.parent / "assets" / "icons")
    for root in roots:
        candidate = root / f"{icon_type}.svg"
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def load_icon_svg(icon_type: str, color: str, size: int = 24) -> str | None:
    """Load an SVG icon file and tint strokes with ``color``. Returns None if missing."""
    path = _icon_asset_path(icon_type)
    if path is None:
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    # Support placeholder or currentColor in asset files
    tinted = (
        raw.replace("#ICON", color)
        .replace("currentColor", color)
        .replace('width="24"', f'width="{size}"')
        .replace('height="24"', f'height="{size}"')
    )
    return tinted


def generate_svg_icon(icon_type: str, color: str, size: int = 24) -> str:
    """Return SVG markup for an icon — prefers ``assets/icons/{name}.svg`` when present."""
    from_file = load_icon_svg(icon_type, color, size)
    if from_file:
        return from_file
    svgs = {
        "settings": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M12 15.5A3.5 3.5 0 1 0 12 8.5a3.5 3.5 0 0 0 0 7z" stroke="{color}" stroke-width="2"/>
            <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.49.49 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96a.49.49 0 0 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58z" stroke="{color}" stroke-width="2"/>
        </svg>''',
        "history": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="9" stroke="{color}" stroke-width="2"/>
            <path d="M12 7v5l3 3" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        "search": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="7" stroke="{color}" stroke-width="2"/>
            <path d="M16 16l5 5" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        "close": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M6 6l12 12M18 6L6 18" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        "chevron": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M9 6l6 6-6 6" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        "chevron_right": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M9 6l6 6-6 6" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        "chevron_down": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M6 9l6 6 6-6" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        "folder": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
        </svg>''',
        "check": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M5 12l5 5L20 7" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        "plus": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M12 5v14M5 12h14" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        "trash": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        "edit": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M15.232 5.232l3.536 3.536M9 13l-2 6 6-2 9.586-9.586a2 2 0 000-2.828l-.708-.708a2 2 0 00-2.828 0L9 13z" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        "bell": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
        "export": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>''',
        "timer": f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="13" r="8" stroke="{color}" stroke-width="2"/>
            <path d="M12 9v4l2 2M10 2h4" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
        </svg>''',
    }
    return svgs.get(icon_type, "")


def search_icon_pixmap(theme: Dict[str, Any], size: int = 16) -> "QPixmap":
    """Shared search magnifier — same asset + amber accent everywhere."""
    color = theme["colors"].get("accent", _c(theme, "text"))
    return svg_to_pixmap(generate_svg_icon("search", color, size), size)


def svg_to_pixmap(svg_str: str, size: int = 24) -> "QPixmap":
    """Convert SVG string to QPixmap."""
    from PyQt6.QtGui import QPainter, QPixmap
    from PyQt6.QtSvg import QSvgRenderer
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(bytearray(svg_str.encode()))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def get_icon_color(theme_id: str) -> str:
    """Get appropriate icon color for theme."""
    theme = get_theme(theme_id)
    return theme["colors"].get("icon", theme["colors"]["text"])


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
    input_size = theme.get("fonts", {}).get("size_input", 14)
    family = theme.get("fonts", {}).get("family") or ""
    family_css = f'font-family: "{family}";' if family else ""
    return f"""
        QLineEdit {{
            background-color: {_c(theme, "input_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "input")}px;
            padding: 8px;
            font-size: {input_size}px;
            {family_css}
            min-height: 32px;
            selection-background-color: {_c(theme, "accent")};
        }}
        QLineEdit:focus {{
            border: 1px solid {_c(theme, "border_highlight")};
        }}
    """


def _combo_dropdown_arrow_svg(theme: Dict[str, Any]) -> str:
    """Downward-pointing chevron as a base64 data URI for the combo box indicator."""
    import base64
    stroke = theme["colors"].get("chrome_icon") or theme["colors"].get("icon") or _c(theme, "text")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 8">'
        f'<path d="M1 1.5l5 5 5-5" fill="none" '
        f'stroke="{stroke}" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round"/></svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"image: url(data:image/svg+xml;base64,{encoded});"


def _combo_popup_bg(theme: Dict[str, Any]) -> str:
    """Solid popup surface — matches dialog shells and inputs, not context menus."""
    return _c(theme, "glass_overlap_solid")


def combo_popup_view_stylesheet(theme: Dict[str, Any]) -> str:
    """QSS for QComboBox list popups (top-level windows that ignore app QSS)."""
    bg = _combo_popup_bg(theme)
    border = _c(theme, "border")
    surface_r = _r(theme, "input")
    item_r = _r(theme, "input")
    return f"""
        QFrame, QWidget, QListView {{
            background-color: {bg};
            color: {_c(theme, "text")};
            border: 1px solid {border};
            border-radius: {surface_r}px;
        }}
        QAbstractItemView {{
            background-color: {bg};
            color: {_c(theme, "text")};
            border: none;
            outline: none;
            padding: 4px;
            font-size: 14px;
            selection-background-color: {_c(theme, "hover_strong")};
            selection-color: {_c(theme, "text")};
        }}
        QAbstractItemView::item {{
            background-color: transparent;
            color: {_c(theme, "text")};
            border: none;
            padding: 6px 10px;
            border-radius: {item_r}px;
            min-height: 20px;
        }}
        QAbstractItemView::item:hover {{
            background-color: {_c(theme, "hover")};
        }}
        QAbstractItemView::item:selected {{
            background-color: {_c(theme, "hover_strong")};
            color: {_c(theme, "text")};
        }}
    """


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
            background-color: {_combo_popup_bg(theme)};
            color: {_c(theme, "text")};
            border: none;
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
    cb = theme.get("spacing", {}).get("checkbox_size", 20)
    return f"""
        QCheckBox {{
            color: {_c(theme, "text")};
            font-size: 14px;
            padding: 5px;
            background: transparent;
            border: none;
            min-height: 24px;
        }}
        QCheckBox QLabel {{
            min-width: 120px;
        }}
        QCheckBox::indicator {{
            width: {cb}px;
            height: {cb}px;
            border-radius: {_r(theme, "checkbox")}px;
            border: 1px solid {_c(theme, "checkbox_border")};
            background-color: {_c(theme, "checkbox_indicator")};
        }}
        QCheckBox::indicator:hover {{
            border: 1px solid {_c(theme, "accent")};
        }}
        QCheckBox::indicator:checked {{
            background-color: {_c(theme, "checkbox_checked")};
            border: 1px solid {_c(theme, "accent")};
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
        QMenu::item#deleteAction {{
            color: {_c(theme, "danger_text")};
        }}
        QMenu::item#deleteAction:selected {{
            background-color: {_c(theme, "danger_hover")};
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
            background: transparent;
            width: 8px;
            margin: 4px 2px 4px 0;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {handle};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {hover};
        }}
        QScrollBar::handle:vertical:pressed {{
            background: {hover_strong};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            background: none;
            border: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
            border: none;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            margin: 0 4px 2px 4px;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: {handle};
            border-radius: 4px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {hover};
        }}
        QScrollBar::handle:horizontal:pressed {{
            background: {hover_strong};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
            background: none;
            border: none;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
            border: none;
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
            padding: 8px 20px;
            font-size: 13px;
            font-weight: 500;
            min-height: 32px;
        }}
        QPushButton:hover {{
            background: {_c(theme, "hover_strong")};
            border: 1px solid {_c(theme, "border_highlight")};
        }}
    """


def calendar_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QCalendarWidget {{
            background: {_c(theme, "menu_bg")};
            color: {_c(theme, "text")};
        }}
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background: {_c(theme, "menu_bg")};
            border-top: 1px solid {_c(theme, "border")};
            border-bottom: 1px solid {_c(theme, "border")};
            padding: 4px;
        }}
        QCalendarWidget QToolButton {{
            color: {_c(theme, "text")};
            background: transparent;
            border: none;
            border-radius: {_r(theme, "small")}px;
            padding: 4px 8px;
            font-size: 13px;
            font-weight: bold;
        }}
        QCalendarWidget QToolButton:hover {{
            background: {_c(theme, "hover")};
        }}
        QCalendarWidget QToolButton:pressed {{
            background: {_c(theme, "hover_strong")};
        }}
        QCalendarWidget QToolButton#qt_calendar_prevmonth {{
            qproperty-icon: none;
            qproperty-text: "\u25C0";
            font-size: 12px;
        }}
        QCalendarWidget QToolButton#qt_calendar_nextmonth {{
            qproperty-icon: none;
            qproperty-text: "\u25B6";
            font-size: 12px;
        }}
        QCalendarWidget QSpinBox {{
            background: {_c(theme, "input_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "small")}px;
            padding: 2px 4px;
            font-size: 13px;
        }}
        QCalendarWidget QSpinBox:hover {{
            border: 1px solid {_c(theme, "border_highlight")};
        }}
        QCalendarWidget QAbstractItemView {{
            background: {_c(theme, "menu_bg")};
            color: {_c(theme, "text")};
            selection-background-color: {_c(theme, "hover_strong")};
            selection-color: {_c(theme, "text")};
            border: none;
            outline: none;
        }}
        QCalendarWidget QAbstractItemView:enabled {{
            color: {_c(theme, "text")};
        }}
        QCalendarWidget QAbstractItemView:disabled {{
            color: {_c(theme, "text_muted")};
        }}
        QCalendarWidget QAbstractItemView:focus {{
            outline: none;
        }}
        QCalendarWidget QWidget#qt_calendar_calendarview {{
            background: {_c(theme, "menu_bg")};
        }}
        QCalendarWidget QToolButton#qt_calendar_monthbutton {{
            font-size: 13px;
            padding: 4px 8px;
            border-radius: {_r(theme, "small")}px;
        }}
        QCalendarWidget QToolButton#qt_calendar_yearbutton {{
            font-size: 13px;
            padding: 4px 8px;
            border-radius: {_r(theme, "small")}px;
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
            font-size: 13px;
            font-weight: 500;
            padding: 8px 20px;
            min-height: 32px;
        }}
        QPushButton#ghostButton:hover {{
            background: {_c(theme, "hover")};
            border: 1px solid {_c(theme, "border_highlight")};
        }}
        QPushButton#ghostButton:pressed {{
            background: {_c(theme, "hover_strong")};
        }}
    """


def accent_icon_button_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QPushButton#accentIconButton {{
            background: {_c(theme, "accent_button_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "border")};
            border-radius: {_r(theme, "button")}px;
            font-size: 18px;
            font-weight: bold;
            padding: 0px;
            min-height: 24px;
        }}
        QPushButton#accentIconButton:hover {{
            background: {_c(theme, "hover_strong")};
            border: 1px solid {_c(theme, "border_highlight")};
        }}
    """


def primary_button_stylesheet(theme: Dict[str, Any]) -> str:
    """Filled amber CTA — accent is reserved for meaning, not translucent white."""
    return f"""
        QPushButton#primaryButton {{
            background: {_c(theme, "accent")};
            color: {_c(theme, "on_accent")};
            border: 1px solid {_c(theme, "accent")};
            border-radius: {_r(theme, "button")}px;
            padding: 8px 20px;
            font-size: 13px;
            font-weight: 600;
            min-height: 32px;
        }}
        QPushButton#primaryButton:hover {{
            background: {_c(theme, "accent_hover")};
            border: 1px solid {_c(theme, "accent_hover")};
        }}
        QPushButton#primaryButton:pressed {{
            background: {_c(theme, "accent_pressed")};
            border: 1px solid {_c(theme, "accent_pressed")};
        }}
        QPushButton#primaryButton:focus {{
            border: 1px solid {_c(theme, "accent_hover")};
        }}
    """


def sidebar_button_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QPushButton#sidebarButton {{
            background: transparent;
            color: {_c(theme, "text")};
            border: 1px solid transparent;
            border-radius: {_r(theme, "button")}px;
            padding: 8px 14px;
            font-size: 13px;
            font-weight: 500;
            min-height: 32px;
            text-align: left;
        }}
        QPushButton#sidebarButton:hover {{
            background: {_c(theme, "hover")};
            border: 1px solid {_c(theme, "border")};
        }}
        QPushButton#sidebarButton:checked {{
            background: {_c(theme, "accent_button_bg")};
            border: 1px solid {_c(theme, "border_highlight")};
            font-weight: 600;
        }}
    """


def danger_button_stylesheet(theme: Dict[str, Any]) -> str:
    return f"""
        QPushButton#dangerButton {{
            background-color: {_c(theme, "danger_bg")};
            color: {_c(theme, "danger_text")};
            border: 1px solid {_c(theme, "danger_border")};
            border-radius: {_r(theme, "button")}px;
            padding: 8px 20px;
            font-size: 13px;
            font-weight: 500;
            min-height: 32px;
        }}
        QPushButton#dangerButton:hover {{
            background-color: {_c(theme, "danger_hover")};
            border: 1px solid {_c(theme, "danger_text")};
        }}
        QPushButton#dangerButton:pressed {{
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
    weight = theme.get("fonts", {}).get("weight_header", 500)
    return f"""
        QPushButton#groupHeader {{
            background: {_c(theme, "group_header_bg")};
            color: {_c(theme, "text")};
            border: 1px solid {_c(theme, "group_header_border")};
            border-radius: {_r(theme, "input")}px;
            padding: 8px 10px;
            text-align: left;
            font-size: 14px;
            font-weight: {weight};
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


def footer_history_button_stylesheet(theme: dict) -> str:
    """Ghost-style footer history control — quieter than a bordered chip."""
    c = theme["colors"]
    return f"""
        QPushButton {{
            background: transparent;
            color: {c.get('text_muted', 'rgba(255,255,255,180)')};
            border: none;
            border-radius: 6px;
            padding: 3px 6px;
            font-size: 10px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            color: {c.get('text', '#ffffff')};
            background: {c.get('hover', 'rgba(255,255,255,15)')};
        }}
    """


def footer_bar_stylesheet(theme: dict) -> str:
    """Stylesheet for the footer bar container."""
    c = theme["colors"]
    return f"""
        QWidget {{
            background: {c.get("input_bg", "rgba(0,0,0,40)")};
            border: none;
            border-radius: 0px;
        }}
    """


def overflow_menu_stylesheet(theme: dict) -> str:
    """Stylesheet for the overflow (···) dropdown menu."""
    c = theme["colors"]
    bg = c.get("menu_bg", "rgba(40, 40, 40, 220)")
    fg = c.get("text", "#ffffff")
    border = c.get("menu_border", "rgba(255,255,255,50)")
    hover = c.get("hover", "rgba(255,255,255,30)")
    return f"""
        QMenu {{
            background: {bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 4px 0;
        }}
        QMenu::item {{
            padding: 6px 24px;
        }}
        QMenu::item:selected {{
            background: {hover};
        }}
    """


def history_header_card_stylesheet(theme: dict) -> str:
    """Stylesheet for the history dialog header card."""
    c = theme["colors"]
    return f"""
        QWidget {{
            background: {c.get('input_bg', 'rgba(0,0,0,40)')};
            border-radius: 12px;
            padding: 12px;
        }}
    """


def history_title_stylesheet(theme: dict) -> str:
    """Stylesheet for the history dialog title label."""
    c = theme["colors"]
    return f"font-weight: bold; font-size: 16px; color: {c.get('text', '#ffffff')}; background: transparent;"


def history_count_badge_stylesheet(theme: dict) -> str:
    """Stylesheet for the history count badge."""
    c = theme["colors"]
    return f"""
        color: {c.get('text', '#ffffff')};
        background: {c.get('hover', 'rgba(255,255,255,10)')};
        border: 1px solid {c.get('border', 'rgba(255,255,255,60)')};
        border-radius: 8px;
        font-size: 10px;
        font-weight: bold;
    """


def history_search_bar_stylesheet(theme: dict) -> str:
    """Stylesheet for the history search bar."""
    c = theme["colors"]
    return f"""
        QLineEdit {{
            background: {c.get('input_bg', 'rgba(0,0,0,40)')};
            color: {c.get('text', '#ffffff')};
            border: 1px solid {c.get('border', 'rgba(255,255,255,60)')};
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 1px solid {c.get('border_highlight', 'rgba(255,255,255,90)')};
        }}
    """


def history_footer_stylesheet(theme: dict) -> str:
    """Stylesheet for the history dialog footer."""
    c = theme["colors"]
    return f"background: {c.get('input_bg', 'rgba(0,0,0,40)')}; border-radius: 12px;"


def history_clear_all_button_stylesheet(theme: dict) -> str:
    """Stylesheet for the Clear All button in history."""
    c = theme["colors"]
    return f"""
        QPushButton {{
            background: transparent;
            color: {c.get('danger_text', '#ff5050')};
            border: 1px solid {c.get('danger_border', 'rgba(255,50,50,80)')};
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 12px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background: {c.get('danger_hover', 'rgba(255,80,80,15)')};
        }}
    """


def settings_scroll_area_stylesheet(theme: dict) -> str:
    """Stylesheet for settings scroll areas."""
    c = theme["colors"]
    return f"""
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {c.get('border', 'rgba(255,255,255,60)')};
            border-radius: 4px;
            min-height: 30px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """


_STYLESHEET_CACHE: dict[str, str] = {}


def build_application_stylesheet(theme: Dict[str, Any] | None = None) -> str:
    """Build (and cache) the application-wide QSS for a theme dict or id."""
    if isinstance(theme, str):
        cache_key = normalize_theme_id(theme)
        cached = _STYLESHEET_CACHE.get(cache_key)
        if cached is not None:
            return cached
        resolved = get_theme(cache_key)
        css = _build_application_stylesheet_uncached(resolved)
        _STYLESHEET_CACHE[cache_key] = css
        return css
    resolved = theme or DARK_THEME
    return _build_application_stylesheet_uncached(resolved)


def _build_application_stylesheet_uncached(theme: Dict[str, Any]) -> str:
    """Full app QSS generated from the theme dictionary."""
    theme = theme or DARK_THEME
    sections = [
        "QMainWindow { background: transparent; }",
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
        calendar_stylesheet(theme),
    ]
    return "\n".join(sections)


def apply_theme_to_app(
    app,
    theme: Dict[str, Any] | str | None = None,
) -> Dict[str, Any]:
    """Apply generated QSS to the QApplication instance."""
    if isinstance(theme, str):
        theme_key = normalize_theme_id(theme)
        resolved = get_theme(theme_key)
        css = build_application_stylesheet(theme_key)
    else:
        resolved = deepcopy(theme or DARK_THEME)
        theme_key = resolved.get("id") or resolved.get("name")
        css = build_application_stylesheet(resolved)

    # Skip identical re-applies (common when settings echo theme_applied).
    if getattr(app, "_nudge_theme_css", None) == css:
        return resolved

    # Set once — clearing first forced a second full app restyle.
    app.setStyleSheet(css)
    app._nudge_theme_css = css

    # Set QPalette so Qt uses proper cursor/selection colors (QSS caret-color is not supported)
    from PyQt6.QtGui import QColor, QPalette
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Text, QColor(_c(resolved, "text")))
    palette.setColor(QPalette.ColorRole.Base, QColor(_c(resolved, "input_bg").replace("rgba", "rgb").replace(", 40)", ", 255)").replace(", 20)", ", 255)").replace(", 210)", ", 255)")))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(_c(resolved, "accent")))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    # Fix combo box dropdown popups — they are top-level windows that don't inherit app QSS
    _style_all_combo_views(resolved, app)

    return resolved


# ── Combo popup styling (top-level windows that ignore app QSS) ──────────────

def _combo_popup_palette(theme: Dict[str, Any]) -> "QPalette":
    from PyQt6.QtGui import QColor, QPalette

    pal = QPalette()
    surface = QColor(_combo_popup_bg(theme))
    text_c = QColor(_c(theme, "text"))
    highlight = QColor(_c(theme, "hover_strong"))
    pal.setColor(QPalette.ColorRole.Base, surface)
    pal.setColor(QPalette.ColorRole.Window, surface)
    pal.setColor(QPalette.ColorRole.Text, text_c)
    pal.setColor(QPalette.ColorRole.Highlight, highlight)
    pal.setColor(QPalette.ColorRole.HighlightedText, text_c)
    return pal


def _apply_combo_popup_surface(combo, theme: Dict[str, Any]) -> None:
    """Apply themed background, border, and palette to an open combo popup."""
    from PyQt6.QtCore import Qt

    try:
        view = combo.view()
        if view is None:
            return
        popup_css = combo_popup_view_stylesheet(theme)
        popup_pal = _combo_popup_palette(theme)
        view.setStyleSheet(popup_css)
        view.setPalette(popup_pal)
        view.setAutoFillBackground(True)
        vp = view.viewport()
        if vp:
            vp.setStyleSheet(f"background-color: {_combo_popup_bg(theme)}; border: none;")
            vp.setPalette(popup_pal)
            vp.setAutoFillBackground(True)
        popup_win = view.window()
        if popup_win is None:
            return
        flags = popup_win.windowFlags()
        popup_win.setWindowFlags(
            flags
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        popup_win.setStyleSheet(popup_css)
        popup_win.setPalette(popup_pal)
        popup_win.setAutoFillBackground(True)
        styler = getattr(combo, "_combo_popup_styler", None)
        if styler is None:
            styler = _ComboPopupStyler(theme, combo, popup_win)
            popup_win.installEventFilter(styler)
            combo._combo_popup_styler = styler
        else:
            styler.update_theme(theme)
        popup_win.show()
    except RuntimeError:
        pass


class _ComboPopupStyler(QObject):
    """Restyle combo popups when the popup window is shown."""

    def __init__(self, theme: Dict[str, Any], combo, parent=None):
        super().__init__(parent)
        self._theme = deepcopy(theme)
        self._combo = combo

    def update_theme(self, theme: Dict[str, Any]) -> None:
        self._theme = deepcopy(theme)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show:
            _apply_combo_popup_surface(self._combo, self._theme)
        return False


def _style_all_combo_views(theme: Dict[str, Any], app=None) -> None:
    """Style every QComboBox dropdown popup to match the current theme.

    Qt combo popups are top-level windows that don't inherit the app stylesheet.
    We monkey-patch showPopup() on each combo so palette + QSS are applied every
    time the list opens, and strip native popup chrome on Windows.
    """
    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtWidgets import QApplication, QComboBox

    if app is None:
        app = QApplication.instance()
    if app is None:
        return

    popup_css = combo_popup_view_stylesheet(theme)

    def _make_show_popup(original_show_popup):
        def _themed_show_popup(self_combo):
            original_show_popup(self_combo)
            styler = getattr(self_combo, "_combo_popup_styler", None)
            active_theme = styler._theme if styler is not None else theme
            _apply_combo_popup_surface(self_combo, active_theme)
        return _themed_show_popup

    for combo in app.findChildren(QComboBox):
        view = combo.view()
        if view is None:
            continue
        view.setStyleSheet(popup_css)
        pal = _combo_popup_palette(theme)
        view.setPalette(pal)
        vp = view.viewport()
        if vp:
            vp.setPalette(pal)
        combo_pal = combo.palette()
        combo_pal.setColor(QPalette.ColorRole.Base, QColor(_c(theme, "input_bg")))
        combo_pal.setColor(QPalette.ColorRole.Text, QColor(_c(theme, "text")))
        combo.setPalette(combo_pal)
        styler = getattr(combo, "_combo_popup_styler", None)
        if styler is not None:
            styler.update_theme(theme)
        if not getattr(combo, "_themed_popup", False):
            combo._themed_popup = True
            combo._original_show_popup = combo.showPopup
            combo.showPopup = _make_show_popup(
                combo._original_show_popup,
            ).__get__(combo, type(combo))


def refresh_glass_shells(
    root: QWidget,
    theme: Dict[str, Any] | str | None = None,
    *,
    polish_all: bool = False,
) -> None:
    """
    Re-apply the glass panel gradient on dialog shells after a global theme change (H7).

    Frameless translucent dialogs may not repaint the outer shell from app QSS alone.
    By default only named glass shells are restyled — recursive polish-all is optional
    because it is O(widgets) and causes visible lag on appearance changes.
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

    if polish_all:
        style = root.style()
        if style is not None:
            all_widgets = [root] + root.findChildren(
                QWidget, options=Qt.FindChildOption.FindChildrenRecursively
            )
            for widget in all_widgets:
                style.unpolish(widget)
                style.polish(widget)
                widget.update()
    else:
        root.update()

    root.update()
