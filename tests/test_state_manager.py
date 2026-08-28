"""Unit tests for StateManager."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
from src.backend.state_manager import StateManager


@pytest.fixture
def state_manager(tmp_path):
    """Create a StateManager with a temp filepath."""
    filepath = tmp_path / "test_appstate.json"
    with patch("src.backend.state_manager.get_data_file", return_value=filepath):
        sm = StateManager("test_appstate.json")
        sm.filepath = filepath
        return sm


class TestStateManagerInit:
    """Tests for StateManager initialization."""

    def test_default_state_has_required_keys(self, state_manager):
        assert "theme" in state_manager.state
        assert "taskTextSize" in state_manager.state
        assert "windowPos" in state_manager.state
        assert "windowSize" in state_manager.state

    def test_default_theme_is_dark(self, state_manager):
        assert state_manager.state["theme"] == "dark"

    def test_default_text_size(self, state_manager):
        assert state_manager.state["taskTextSize"] == 14


class TestStateManagerLoad:
    """Tests for StateManager.load()."""

    def test_load_empty_file_returns_defaults(self, state_manager):
        result = state_manager.load()
        assert result == state_manager.state

    def test_load_existing_file(self, state_manager):
        state_manager.filepath.write_text(
            json.dumps({"theme": "light", "taskTextSize": 18}),
            encoding="utf-8"
        )
        result = state_manager.load()
        assert result["theme"] == "light"
        assert result["taskTextSize"] == 18

    def test_load_corrupted_json_returns_defaults(self, state_manager):
        state_manager.filepath.write_text("not valid json{", encoding="utf-8")
        result = state_manager.load()
        assert result == state_manager.state  # Falls back to defaults

    def test_load_nonexistent_file_returns_defaults(self, tmp_path):
        filepath = tmp_path / "nonexistent.json"
        with patch("src.backend.state_manager.get_data_file", return_value=filepath):
            sm = StateManager("nonexistent.json")
            sm.filepath = filepath
            result = sm.load()
            assert result == sm.state


class TestStateManagerSave:
    """Tests for StateManager.save()."""

    def test_save_creates_file(self, state_manager):
        state_manager.save()
        state_manager.flush()
        assert state_manager.filepath.exists()

    def test_save_persists_data(self, state_manager):
        state_manager.state["theme"] = "light"
        state_manager.save()
        state_manager.flush()
        # Load in a new StateManager
        with patch("src.backend.state_manager.get_data_file", return_value=state_manager.filepath):
            sm2 = StateManager("test_appstate.json")
            sm2.filepath = state_manager.filepath
            sm2.load()
            assert sm2.state["theme"] == "light"

    def test_save_is_atomic(self, state_manager):
        """Verify atomic write doesn't leave temp files."""
        state_manager.save()
        state_manager.flush()
        # Check no .tmp files remain
        temp_files = list(state_manager.filepath.parent.glob("*.tmp"))
        assert len(temp_files) == 0


class TestWindowGeometry:
    """Tests for window geometry methods."""

    def test_get_window_geometry_returns_tuple(self, state_manager):
        result = state_manager.get_window_geometry()
        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_save_window_geometry(self, state_manager):
        state_manager.save_window_geometry(200, 300, 400, 500)
        assert state_manager.state["windowPos"]["x"] == 200
        assert state_manager.state["windowPos"]["y"] == 300
        assert state_manager.state["windowSize"]["w"] == 400
        assert state_manager.state["windowSize"]["h"] == 500

    def test_get_history_window_size(self, state_manager):
        result = state_manager.get_history_window_size()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_get_settings_window_size(self, state_manager):
        result = state_manager.get_settings_window_size()
        assert isinstance(result, tuple)
        assert len(result) == 2
