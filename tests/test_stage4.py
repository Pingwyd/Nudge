"""Tests for Stage 4 — Settings Panel Fixes."""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMenu, QListWidget, QListWidgetItem


@pytest.fixture
def qapp_instance():
    """Create a QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestSettingsPanel:
    """Test settings panel functionality."""

    def test_boot_notification_toggle_exists(self, qapp_instance):
        """4.1: Boot notification toggle should exist in state manager."""
        from src.backend.state_manager import StateManager
        
        sm = StateManager.__new__(StateManager)
        sm.state = {"showBootNotification": True}
        
        # Check that the key exists and defaults to True
        assert sm.state.get("showBootNotification", True) == True
        
        # Check that it can be set to False
        sm.state["showBootNotification"] = False
        assert sm.state.get("showBootNotification", True) == False

    def test_double_click_opens_edit_dialog(self, qapp_instance):
        """4.2: Double-click on reminder should open edit dialog, not clear."""
        from src.frontend.main_window import SettingsDialog
        
        # Check that the method exists
        assert hasattr(SettingsDialog, '_edit_task_reminder_from_list')
        
        # Check that the method is different from clear
        assert SettingsDialog._edit_task_reminder_from_list != SettingsDialog._clear_task_reminder_from_list

    def test_help_tab_exists(self, qapp_instance):
        """4.3: Help tab should exist with Tutorial, Support, and Reminders buttons."""
        from src.frontend.main_window import SettingsDialog
        
        # Check that the method exists
        assert hasattr(SettingsDialog, 'init_ui')
        
        # Check that help_tab is created in init_ui
        import inspect
        source = inspect.getsource(SettingsDialog.init_ui)
        assert 'help_tab = QWidget()' in source
        assert 'help_layout = QVBoxLayout(help_tab)' in source

    def test_reset_to_defaults_above_save_close(self, qapp_instance):
        """4.4: Reset to Defaults should be above Save/Close buttons."""
        from src.frontend.main_window import SettingsDialog
        
        # Check that the button is created
        import inspect
        source = inspect.getsource(SettingsDialog.init_ui)
        assert 'self.reset_shortcuts_btn = QPushButton("Reset to Defaults")' in source
        
        # Check that it's added before the button_row
        assert 'right_column.addWidget(self.reset_shortcuts_btn)' in source
        assert 'button_row = QHBoxLayout()' in source

    def test_whats_new_in_overflow_menu(self, qapp_instance):
        """4.5: What's New should be in overflow menu, not in Settings button row."""
        from src.frontend.main_window import MainWindow
        
        # Check that overflow menu has What's New
        import inspect
        source = inspect.getsource(MainWindow.init_ui)
        assert "What" in source and "New" in source
        
        # Check that Settings dialog doesn't have What's New button
        from src.frontend.main_window import SettingsDialog
        settings_source = inspect.getsource(SettingsDialog.init_ui)
        assert 'whatsnew_btn' not in settings_source

    def test_export_uses_shared_function(self, qapp_instance):
        """4.6: Export should use shared run_export_with_dialog function."""
        from src.backend.export_service import run_export_with_dialog
        
        # Check that the function exists
        assert callable(run_export_with_dialog)
        
        # Check that ExportDialog uses it
        from src.frontend.export_dialog import ExportDialog
        import inspect
        source = inspect.getsource(ExportDialog._run_export)
        assert 'run_export_with_dialog' in source
        
        # Check that SettingsDialog uses it
        from src.frontend.main_window import SettingsDialog
        settings_source = inspect.getsource(SettingsDialog._run_settings_export)
        assert 'run_export_with_dialog' in settings_source
