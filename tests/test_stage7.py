"""
Tests for Stage 7 — Visual & Theme Completion.

7.1 OLED Theme
7.2 accent/muted tokens in all themes
7.3 Opacity slider floor 30%
7.4 Pin to Desktop / Always on Top mutual exclusion + note
7.5 Empty state UI
"""

import pytest
import inspect
from src.frontend.theme import DARK_THEME, LIGHT_THEME, OLED_THEME, THEME_BY_ID, get_theme


@pytest.fixture
def qapp_instance():
    """Create a QApplication instance for tests."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


# ── 7.1 OLED Theme ─────────────────────────────────────────────────────

class TestOLEDTheme:
    def test_oled_in_theme_by_id(self):
        assert "oled" in THEME_BY_ID

    def test_oled_background_is_pure_black(self):
        assert OLED_THEME["colors"]["glass_start"] == "rgba(0, 0, 0, 255)"
        assert OLED_THEME["colors"]["glass_end"] == "rgba(0, 0, 0, 255)"
        assert OLED_THEME["colors"]["glass_overlap_solid"] == "rgba(0, 0, 0, 255)"

    def test_oled_menu_bg_is_pure_black(self):
        assert OLED_THEME["colors"]["menu_bg"] == "rgba(0, 0, 0, 255)"

    def test_oled_has_all_required_keys(self):
        required = [
            "text", "text_muted", "glass_start", "glass_end", "border",
            "border_highlight", "input_bg", "menu_bg", "menu_border",
            "hover", "hover_strong", "chrome_hover", "chrome_separator",
            "tab_bg", "tab_selected", "group_header_bg", "group_header_border",
            "group_header_hover", "accent_button_bg", "checkbox_indicator",
            "checkbox_checked", "checkbox_border", "danger_bg", "danger_border",
            "danger_hover", "danger_text", "scrollbar", "scrollbar_track",
            "tooltip_bg", "tooltip_border", "separator", "drop_indicator",
            "glass_overlap_solid", "accent", "muted",
        ]
        for key in required:
            assert key in OLED_THEME["colors"], f"Missing key: {key}"

    def test_oled_get_theme_returns_valid(self):
        theme = get_theme("oled")
        assert theme["id"] == "oled"
        assert "colors" in theme
        assert "radii" in theme
        assert "fonts" in theme

    def test_oled_radii_match_dark(self):
        assert OLED_THEME["radii"] == DARK_THEME["radii"]


# ── 7.2 accent and muted tokens in all themes ──────────────────────────

class TestAccentMutedTokens:
    def test_dark_has_accent(self):
        assert "accent" in DARK_THEME["colors"]

    def test_dark_has_muted(self):
        assert "muted" in DARK_THEME["colors"]

    def test_light_has_accent(self):
        assert "accent" in LIGHT_THEME["colors"]

    def test_light_has_muted(self):
        assert "muted" in LIGHT_THEME["colors"]

    def test_oled_has_accent(self):
        assert "accent" in OLED_THEME["colors"]

    def test_oled_has_muted(self):
        assert "muted" in OLED_THEME["colors"]

    def test_dark_accent_is_valid_color(self):
        accent = DARK_THEME["colors"]["accent"]
        assert accent.startswith("#") or accent.startswith("rgb")

    def test_light_accent_is_valid_color(self):
        accent = LIGHT_THEME["colors"]["accent"]
        assert accent.startswith("#") or accent.startswith("rgb")


# ── 7.3 Opacity slider floor 30% ──────────────────────────────────────

class TestOpacitySliderFloor:
    def test_opaque_constants_floor(self):
        from src.constants import OPACITY_SLIDER_MIN, OPACITY_FLOOR
        assert OPACITY_SLIDER_MIN == 30
        assert OPACITY_FLOOR == 0.30

    def test_settings_dialog_opacity_slider_minimum_in_source(self):
        """Verify the slider minimum is 30 in source code."""
        from src.frontend.settings_dialog import SettingsDialog
        from src.constants import OPACITY_SLIDER_MIN
        source = inspect.getsource(SettingsDialog.init_ui)
        assert f'OPACITY_SLIDER_MIN)' in source or f'setMinimum({OPACITY_SLIDER_MIN})' in source

    def test_settings_dialog_clamps_low_opacity(self):
        """Verify persisted value below 0.30 is clamped to 0.30."""
        from src.frontend.settings_dialog import SettingsDialog
        from src.constants import OPACITY_SLIDER_MIN
        source = inspect.getsource(SettingsDialog.init_ui)
        assert f'max(OPACITY_SLIDER_MIN' in source or f'max({OPACITY_SLIDER_MIN}' in source


# ── 7.4 Pin to Desktop / Always on Top mutual exclusion ────────────────

class TestPinTopMutualExclusion:
    def test_mutual_exclusion_note_in_source(self):
        """The mutual exclusion logic should exist in the SettingsDialog."""
        from src.frontend.settings_dialog import SettingsDialog
        assert hasattr(SettingsDialog, '_on_pin_to_desktop_toggled')
        assert hasattr(SettingsDialog, '_on_always_on_top_toggled')

    def test_checkbox_uncheck_handlers_exist(self):
        """Handlers for mutual exclusion should exist."""
        from src.frontend.settings_dialog import SettingsDialog
        assert hasattr(SettingsDialog, '_on_pin_to_desktop_toggled')
        assert hasattr(SettingsDialog, '_on_always_on_top_toggled')

    def test_checkbox_handler_blocks_signals(self):
        """Both handlers should block signals to prevent recursion."""
        from src.frontend.settings_dialog import SettingsDialog
        pin_src = inspect.getsource(SettingsDialog._on_pin_to_desktop_toggled)
        top_src = inspect.getsource(SettingsDialog._on_always_on_top_toggled)
        assert 'blockSignals(True)' in pin_src
        assert 'blockSignals(True)' in top_src


# ── 7.5 Empty state UI ────────────────────────────────────────────────

class TestEmptyStateUI:
    def test_empty_state_widgets_created_in_init_ui(self):
        """Verify empty state widgets are created in MainWindow.init_ui."""
        from src.frontend.main_window import MainWindow
        source = inspect.getsource(MainWindow.init_ui)
        assert '_empty_state_widget' in source
        assert '_empty_state_label' in source
        assert '_empty_state_arrow' in source

    def test_empty_state_label_text(self):
        """Verify the empty state label has the correct text."""
        from src.frontend.main_window import MainWindow
        source = inspect.getsource(MainWindow.init_ui)
        assert 'Add a task to get started' in source

    def test_update_empty_state_method_exists(self):
        """Verify _update_empty_state method exists."""
        from src.frontend.main_window import MainWindow
        assert hasattr(MainWindow, '_update_empty_state')

    def test_render_tasks_calls_update_empty_state(self):
        """Verify render_tasks calls _update_empty_state."""
        from src.frontend.task_controller import TaskController
        source = inspect.getsource(TaskController.render_tasks)
        assert '_update_empty_state' in source

    def test_remove_task_calls_update_empty_state(self):
        """Verify _remove_task_row_widget calls _update_empty_state."""
        from src.frontend.task_controller import TaskController
        source = inspect.getsource(TaskController._remove_task_row_widget)
        assert '_update_empty_state' in source

    def test_animate_arrow_method_exists(self):
        """Verify _animate_empty_arrow method exists."""
        from src.frontend.main_window import MainWindow
        assert hasattr(MainWindow, '_animate_empty_arrow')

    def test_empty_state_timer_created(self):
        """Verify QTimer for arrow animation is created."""
        from src.frontend.main_window import MainWindow
        source = inspect.getsource(MainWindow.init_ui)
        assert '_empty_state_timer' in source
