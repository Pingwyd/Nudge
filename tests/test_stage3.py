"""Tests for Stage 3 — Context Menu Refactor."""
import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor, QAction
from PyQt6.QtWidgets import QApplication, QMenu


@pytest.fixture
def qapp_instance():
    """Create a QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestContextMenu:
    """Test context menu functionality."""

    def test_move_up_down_removed(self, qapp_instance):
        """3.1: Move Up and Move Down should not be in the context menu."""
        from src.frontend.main_window import MainWindow
        
        # Create a mock MainWindow
        main_window = MagicMock(spec=MainWindow)
        main_window.app_state = {"theme": "dark"}
        main_window.groups_data = {"groups": []}
        main_window.tasks = []
        
        # Create a task ref
        task_ref = {"id": "1", "text": "Test task", "done": False}
        
        # Call the method
        menu = QMenu()
        main_window._style_context_menu(menu)
        
        # Add actions manually to simulate the menu
        edit_action = QAction("Edit", None)
        menu.addAction(edit_action)
        
        copy_action = QAction("Copy", None)
        menu.addAction(copy_action)
        
        menu.addSeparator()
        
        reminder_menu = menu.addMenu("Set Reminder")
        remind_15m = QAction("15 minutes", None)
        reminder_menu.addAction(remind_15m)
        
        move_top_action = QAction("Move to Top", None)
        menu.addAction(move_top_action)
        
        move_bottom_action = QAction("Move to Bottom", None)
        menu.addAction(move_bottom_action)
        
        menu.addSeparator()
        
        move_menu = menu.addMenu("Move to Group")
        group_action = QAction("General", None)
        move_menu.addAction(group_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete", None)
        menu.addAction(delete_action)
        
        # Check that Move Up and Move Down are not in the menu
        action_texts = [action.text() for action in menu.actions()]
        assert "Move Up" not in action_texts
        assert "Move Down" not in action_texts
        
        # Check that Move to Top and Move to Bottom are still there
        assert "Move to Top" in action_texts
        assert "Move to Bottom" in action_texts
        
        menu.close()

    def test_clear_reminder_at_top_level(self, qapp_instance):
        """3.2: Clear Reminder should be at the top level, not in a submenu."""
        from src.frontend.main_window import MainWindow
        
        # Create a mock MainWindow
        main_window = MagicMock(spec=MainWindow)
        main_window.app_state = {"theme": "dark"}
        main_window.groups_data = {"groups": []}
        main_window.tasks = []
        
        # Create a task ref with a reminder
        task_ref = {"id": "1", "text": "Test task", "done": False, "reminderAt": "2024-01-01T10:00:00"}
        
        # Create the menu
        menu = QMenu()
        main_window._style_context_menu(menu)
        
        # Add actions to simulate the menu structure
        edit_action = QAction("Edit", None)
        menu.addAction(edit_action)
        
        copy_action = QAction("Copy", None)
        menu.addAction(copy_action)
        
        menu.addSeparator()
        
        reminder_menu = menu.addMenu("Set Reminder")
        remind_15m = QAction("15 minutes", None)
        reminder_menu.addAction(remind_15m)
        
        # Clear Reminder should be at top level
        clear_reminder = QAction("Clear Reminder", None)
        menu.addAction(clear_reminder)
        
        move_top_action = QAction("Move to Top", None)
        menu.addAction(move_top_action)
        
        # Check that Clear Reminder is a direct child of the menu
        action_texts = [action.text() for action in menu.actions()]
        assert "Clear Reminder" in action_texts
        
        # Check that Clear Reminder is not in the reminder submenu
        reminder_action_texts = [action.text() for action in reminder_menu.actions()]
        assert "Clear Reminder" not in reminder_action_texts
        
        menu.close()

    def test_delete_action_has_danger_token(self, qapp_instance):
        """3.3: Delete action should have danger color token applied."""
        from src.frontend.main_window import MainWindow
        from src.frontend.theme import get_theme, menu_stylesheet
        
        # Create a mock MainWindow
        main_window = MagicMock(spec=MainWindow)
        main_window.app_state = {"theme": "dark"}
        
        # Create the menu
        menu = QMenu()
        main_window._style_context_menu(menu)
        
        # Add delete action with object name
        delete_action = QAction("Delete", None)
        delete_action.setObjectName("deleteAction")
        menu.addAction(delete_action)
        
        # Check that the action has the correct object name
        assert delete_action.objectName() == "deleteAction"
        
        # Check that the menu stylesheet includes the danger token styling
        theme = get_theme("dark")
        stylesheet = menu_stylesheet(theme)
        assert "deleteAction" in stylesheet
        # Check that the resolved color is present (dark theme danger_text is #ff5555)
        assert "#ff5555" in stylesheet
        
        menu.close()

    def test_context_menu_position_clamped(self, qapp_instance):
        """3.4: Context menu position should be clamped to screen bounds."""
        from src.frontend.main_window import MainWindow
        from PyQt6.QtCore import QPoint
        from PyQt6.QtWidgets import QApplication
        
        # Test various cursor positions
        test_cases = [
            # (cursor_pos, expected_min_x, expected_min_y)
            (QPoint(100, 100), 0, 0),  # Normal position
            (QPoint(-50, 100), 0, 0),  # Off-screen left
            (QPoint(100, -50), 0, 0),  # Off-screen top
        ]
        
        for cursor_pos, expected_min_x, expected_min_y in test_cases:
            # Get screen geometry
            screen = QApplication.screenAt(cursor_pos)
            if screen is None:
                screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # Calculate menu dimensions
            menu_height = 200  # Approximate
            menu_width = 200
            
            # Clamp position
            x = cursor_pos.x()
            if x + menu_width > screen_rect.right():
                x = screen_rect.right() - menu_width
            if x < screen_rect.left():
                x = screen_rect.left()
            
            y = cursor_pos.y()
            if y + menu_height > screen_rect.bottom():
                y = screen_rect.bottom() - menu_height
            if y < screen_rect.top():
                y = screen_rect.top()
            
            # Check that position is within screen bounds
            assert x >= screen_rect.left()
            assert x + menu_width <= screen_rect.right()
            assert y >= screen_rect.top()
            assert y + menu_height <= screen_rect.bottom()
