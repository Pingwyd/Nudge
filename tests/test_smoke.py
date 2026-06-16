"""
Smoke tests — verify every major module imports without error.

This is the regression baseline. If any of these fail, the build is broken.
"""
import pytest


def test_import_constants():
    import src.constants
    assert hasattr(src.constants, "MAIN_WINDOW_DEFAULT")
    assert hasattr(src.constants, "OPACITY_FLOOR")


def test_import_theme():
    from src.frontend.theme import (
        DARK_THEME,
        LIGHT_THEME,
        get_theme,
        normalize_theme_id,
        build_application_stylesheet,
        glass_overlap_stylesheet,
    )
    assert "colors" in DARK_THEME
    assert "colors" in LIGHT_THEME
    assert get_theme("dark") == DARK_THEME
    assert get_theme("light") == LIGHT_THEME
    assert normalize_theme_id(None) == "dark"
    assert normalize_theme_id("invalid") == "dark"
    qss = build_application_stylesheet(DARK_THEME)
    assert len(qss) > 100


def test_import_window_geometry():
    from src.backend.window_geometry import (
        DEFAULT_WINDOW_WIDTH,
        DEFAULT_WINDOW_HEIGHT,
        MIN_WINDOW_WIDTH,
        MIN_WINDOW_HEIGHT,
    )
    assert DEFAULT_WINDOW_WIDTH > 0
    assert DEFAULT_WINDOW_HEIGHT > 0
    assert MIN_WINDOW_WIDTH <= DEFAULT_WINDOW_WIDTH
    assert MIN_WINDOW_HEIGHT <= DEFAULT_WINDOW_HEIGHT


def test_import_frameless_chrome():
    from src.frontend.frameless_chrome import (
        FramelessChromeController,
        RESIZE_MARGIN,
        TITLE_BAR_DRAG_HEIGHT,
    )
    assert RESIZE_MARGIN > 0
    assert TITLE_BAR_DRAG_HEIGHT > 0


def test_import_responsive_text():
    from src.frontend.responsive_text import min_text_column_width
    assert min_text_column_width(100) >= 100
    assert min_text_column_width(500) >= 100


def test_import_state_manager():
    from src.backend.state_manager import StateManager
    assert StateManager is not None


def test_import_updater():
    from src.backend.updater import (
        download_update,
        perform_update,
        parse_changelog,
        FRIENDLY_CHANGELOGS,
    )
    assert callable(download_update)
    assert callable(perform_update)
    assert callable(parse_changelog)
    assert isinstance(FRIENDLY_CHANGELOGS, dict)


def test_import_timer_manager():
    from src.backend.timer_manager import TimerManager, TimerConfig
    assert TimerManager is not None
    assert TimerConfig is not None


def test_import_export_service():
    from src.backend.export_service import ExportRequest
    assert ExportRequest is not None


def test_import_task_store():
    from src.backend.task_store import TaskStore
    assert TaskStore is not None


def test_import_group_store():
    from src.backend.group_store import GroupStore
    assert GroupStore is not None


def test_import_input_parser():
    from src.backend.input_parser import InputParser
    assert InputParser is not None


def test_import_paths():
    from src.backend.paths import get_data_dir, get_data_file
    assert callable(get_data_dir)
    assert callable(get_data_file)


def test_import_icon():
    from src.backend.icon import get_app_icon
    assert callable(get_app_icon)


def test_import_crash_reporter():
    from src.backend.crash_reporter import write_crash_log
    assert callable(write_crash_log)


def test_import_boot_checker():
    from src.backend.boot_checker import BootChecker
    assert BootChecker is not None


def test_import_single_instance():
    from src.backend.single_instance import try_lock
    assert callable(try_lock)


def test_import_system_tray():
    from src.os_layer.system_tray import SystemTrayManager
    assert SystemTrayManager is not None


def test_import_platform_utils():
    from src.os_layer.platform_utils import is_windows, is_macos, is_linux
    assert callable(is_windows)
    assert callable(is_macos)
    assert callable(is_linux)


def test_import_desktop_pin():
    from src.os_layer.desktop_pin import pin_to_desktop
    assert callable(pin_to_desktop)


# ── Frontend module imports (require QApplication) ────────────────────


def test_import_main_window(qapp_instance):
    from src.frontend.main_window import MainWindow
    assert MainWindow is not None


def test_import_themed_message_dialog(qapp_instance):
    from src.frontend.themed_message_dialog import ThemedMessageDialog
    assert ThemedMessageDialog is not None


def test_import_update_dialog(qapp_instance):
    from src.frontend.update_dialog import UpdateInfoDialog, DownloadDialog
    assert UpdateInfoDialog is not None
    assert DownloadDialog is not None


def test_import_timer_dialog(qapp_instance):
    from src.frontend.timer_dialog import TimerDialog
    assert TimerDialog is not None


def test_import_export_dialog(qapp_instance):
    from src.frontend.export_dialog import ExportDialog
    assert ExportDialog is not None


def test_import_crash_dialog(qapp_instance):
    from src.frontend.crash_dialog import CrashDialog
    assert CrashDialog is not None


def test_import_whats_new_dialog(qapp_instance):
    from src.frontend.whats_new_dialog import WhatsNewDialog
    assert WhatsNewDialog is not None


def test_import_support_dialog(qapp_instance):
    from src.frontend.support_dialog import SupportDialog
    assert SupportDialog is not None


def test_import_feedback_dialog(qapp_instance):
    from src.frontend.feedback_dialog import FeedbackDialog
    assert FeedbackDialog is not None


def test_import_task_group_section(qapp_instance):
    from src.frontend.task_group_section import TaskGroupSection
    assert TaskGroupSection is not None


def test_import_history_row(qapp_instance):
    from src.frontend.history_row import HistoryRowWidget
    assert HistoryRowWidget is not None
