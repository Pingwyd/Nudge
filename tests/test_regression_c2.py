"""Regression test for C2: wrong import path in _apply_theme_checkbox."""

import sys
import pytest
from unittest.mock import patch

# Need QApplication for QWidget
from PyQt6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_apply_theme_checkbox_defaults_to_dark_when_none(qapp):
    """_apply_theme_checkbox should default to 'dark' when theme_id is None."""
    from src.frontend.task_row import TaskRowWidget
    row = TaskRowWidget("test task")
    row._apply_theme_checkbox(None)
    assert row._checkbox.styleSheet() != ""


def test_apply_theme_checkbox_accepts_explicit_theme(qapp):
    """_apply_theme_checkbox should work with explicit theme_id."""
    from src.frontend.task_row import TaskRowWidget
    row = TaskRowWidget("test task")
    row._apply_theme_checkbox("dark")
    assert row._checkbox.styleSheet() != ""
    row._apply_theme_checkbox("light")
    assert row._checkbox.styleSheet() != ""


def test_apply_theme_checkbox_no_wrong_import(qapp):
    """_apply_theme_checkbox should NOT import from src.frontend.state_manager."""
    from src.frontend.task_row import TaskRowWidget
    row = TaskRowWidget("test task")
    # After fix, the wrong import path should not exist in the method
    import inspect
    source = inspect.getsource(row._apply_theme_checkbox)
    assert "from src.frontend.state_manager" not in source
    assert "from src.backend.state_manager" not in source
    # Should just default to "dark" without importing StateManager
    row._apply_theme_checkbox(None)
    assert row._checkbox.styleSheet() != ""
