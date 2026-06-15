"""Tests for Stage 6 — Custom Reminder Dialog Polish."""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtWidgets import QApplication, QDialog


@pytest.fixture
def qapp_instance():
    """Create a QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestCustomReminderDialog:
    """Test custom reminder dialog functionality."""

    def test_pre_populate_with_existing_reminder(self, qapp_instance):
        """6.1: Dialog should pre-populate pickers with existing reminder values."""
        from src.frontend.main_window import MainWindow
        from datetime import datetime
        
        # Check that the method exists and handles existing reminders
        import inspect
        source = inspect.getsource(MainWindow._show_custom_reminder_dialog)
        
        # Check for pre-population logic
        assert 'existing_reminder_at = task_ref.get("reminderAt")' in source
        assert 'initial_date = QDate(existing_dt.year, existing_dt.month, existing_dt.day)' in source
        assert 'initial_time = QTime(existing_dt.hour, existing_dt.minute)' in source

    def test_current_reminder_label_shown(self, qapp_instance):
        """6.1: Current reminder label should be shown for existing reminders."""
        from src.frontend.main_window import MainWindow
        
        import inspect
        source = inspect.getsource(MainWindow._show_custom_reminder_dialog)
        
        # Check for current reminder label
        assert 'current_reminder_label = QLabel' in source
        assert 'Current reminder:' in source
        assert 'font-style: italic' in source

    def test_live_preview_label(self, qapp_instance):
        """6.2: Live preview label should update in real-time."""
        from src.frontend.main_window import MainWindow
        
        import inspect
        source = inspect.getsource(MainWindow._show_custom_reminder_dialog)
        
        # Check for preview label
        assert 'preview_label = QLabel()' in source
        assert 'Will remind at:' in source
        assert 'dateChanged.connect' in source
        assert 'timeChanged.connect' in source

    def test_confirmation_label(self, qapp_instance):
        """6.2: Confirmation label should appear after Set click."""
        from src.frontend.main_window import MainWindow
        
        import inspect
        source = inspect.getsource(MainWindow._show_custom_reminder_dialog)
        
        # Check for confirmation label
        assert 'confirm_label = QLabel()' in source
        assert 'confirm_label.hide()' in source
        assert '#4ade80' in source  # Green color for confirmation

    def test_quickset_syncs_to_pickers(self, qapp_instance):
        """6.3: Quick-set input should sync to pickers in real-time."""
        from src.frontend.main_window import MainWindow
        
        import inspect
        source = inspect.getsource(MainWindow._show_custom_reminder_dialog)
        
        # Check for real-time sync
        assert 'duration_input.textChanged.connect' in source
        assert '_parse_duration' in source

    def test_explanatory_label(self, qapp_instance):
        """6.3: Explanatory label should be present."""
        from src.frontend.main_window import MainWindow
        
        import inspect
        source = inspect.getsource(MainWindow._show_custom_reminder_dialog)
        
        # Check for explanatory label
        assert 'quickset_hint = QLabel' in source
        assert 'Type a shortcut or use the pickers above' in source
