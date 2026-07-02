"""Integration tests for core task flows."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


class TestTaskFlow:
    """Test the full task lifecycle: create -> edit -> complete -> history -> restore."""

    def test_create_task(self, tmp_path):
        """Task creation writes to the store."""
        from src.backend.task_store import TaskStore
        filepath = tmp_path / "tasks.json"
        with patch("src.backend.task_store.get_data_file", return_value=filepath):
            store = TaskStore("tasks.json")
            store.filepath = filepath

        task = {
            "id": "test-1",
            "text": "Buy groceries",
            "done": False,
            "createdAt": "2026-06-29T10:00:00",
            "order": 0,
            "dueDate": None,
            "priority": None,
            "tags": [],
            "recurrence": None,
        }
        store.append_and_save(task)

        loaded = store.load()
        assert len(loaded) == 1
        assert loaded[0]["text"] == "Buy groceries"

    def test_create_and_complete_task(self, tmp_path):
        """Task can be created and then archived (completed)."""
        from src.backend.task_store import TaskStore
        filepath = tmp_path / "tasks.json"
        with patch("src.backend.task_store.get_data_file", return_value=filepath):
            store = TaskStore("tasks.json")
            store.filepath = filepath

        task = {
            "id": "test-2",
            "text": "Write report",
            "done": False,
            "createdAt": "2026-06-29T10:00:00",
            "order": 0,
            "dueDate": None,
            "priority": None,
            "tags": [],
            "recurrence": None,
        }
        store.append_and_save(task)
        tasks = store.load()
        assert len(tasks) == 1

        tasks[0]["done"] = True
        store.save(tasks)

        loaded = store.load()
        assert loaded[0]["done"] is True

    def test_multiple_tasks_ordering(self, tmp_path):
        """Multiple tasks maintain insertion order."""
        from src.backend.task_store import TaskStore
        filepath = tmp_path / "tasks.json"
        with patch("src.backend.task_store.get_data_file", return_value=filepath):
            store = TaskStore("tasks.json")
            store.filepath = filepath

        for i in range(5):
            store.append_and_save({
                "id": f"task-{i}",
                "text": f"Task {i}",
                "done": False,
                "createdAt": f"2026-06-29T10:0{i}:00",
                "order": i,
                "dueDate": None,
                "priority": None,
                "tags": [],
                "recurrence": None,
            })

        tasks = store.load()
        assert len(tasks) == 5
        assert [t["text"] for t in tasks] == [f"Task {i}" for i in range(5)]

    def test_task_schema_migration(self, tmp_path):
        """Old tasks without new fields get defaults via _ensure_schema."""
        from src.backend.task_store import TaskStore
        filepath = tmp_path / "tasks.json"

        old_tasks = [{"id": "old-1", "text": "Old task", "done": False}]
        filepath.write_text(json.dumps(old_tasks), encoding="utf-8")

        with patch("src.backend.task_store.get_data_file", return_value=filepath):
            store = TaskStore("tasks.json")
            store.filepath = filepath
            tasks = store.load()

        assert len(tasks) == 1
        assert tasks[0]["dueDate"] is None
        assert tasks[0]["priority"] is None
        assert tasks[0]["tags"] == []
        assert tasks[0]["recurrence"] is None


class TestInputParserIntegration:
    """Test InputParser with various real-world inputs."""

    def test_complex_input(self):
        """Parse input with priority, tags, and multiple sentences."""
        from src.backend.input_parser import InputParser

        result = InputParser.parse_input("! Buy groceries and #work prepare presentation. Call dentist.")

        assert result[0]["priority"] == "high"
        assert "work" in result[0]["tags"]
        assert "Buy groceries" in result[0]["text"]

    def test_recurrence_input(self):
        """Recurrence is preserved through the pipeline."""
        from src.backend.recurrence_manager import RecurrenceManager

        task = {
            "id": "rec-1",
            "text": "Weekly standup",
            "dueDate": "2026-07-01",
            "recurrence": {"type": "weekly", "interval": 1},
        }

        assert RecurrenceManager.should_recreate(task) is True

        next_task = RecurrenceManager.create_next_instance(task)
        assert next_task["dueDate"] == "2026-07-08"
        assert next_task["recurrence"] == {"type": "weekly", "interval": 1}
        assert next_task["id"] != task["id"]


class TestStateManagerIntegration:
    """Test StateManager atomic operations."""

    def test_concurrent_saves(self, tmp_path):
        """Multiple saves don't corrupt the file."""
        from src.backend.state_manager import StateManager
        filepath = tmp_path / "state.json"
        with patch("src.backend.state_manager.get_data_file", return_value=filepath):
            sm = StateManager("state.json")
            sm.filepath = filepath

        for i in range(10):
            sm.state["test_key"] = f"value_{i}"
            sm.save()

        with patch("src.backend.state_manager.get_data_file", return_value=filepath):
            loaded = StateManager("state.json")
            loaded.filepath = filepath
            loaded.load()
        assert loaded.state["test_key"] == "value_9"

    def test_corrupted_state_recovery(self, tmp_path):
        """Corrupted state file returns defaults."""
        from src.backend.state_manager import StateManager
        filepath = tmp_path / "state.json"
        filepath.write_text("NOT VALID JSON {{{", encoding="utf-8")

        with patch("src.backend.state_manager.get_data_file", return_value=filepath):
            sm = StateManager("state.json")
            sm.filepath = filepath
            sm.load()
        assert "theme" in sm.state


class TestGroupStoreIntegration:
    """Test GroupStore operations."""

    def test_group_lifecycle(self, tmp_path):
        """Create, rename, and delete groups."""
        from src.backend.group_store import GroupStore
        from src.backend.task_groups import create_group
        filepath = tmp_path / "groups.json"
        with patch("src.backend.group_store.get_data_file", return_value=filepath):
            gs = GroupStore("groups.json")
            gs.filepath = filepath

        data = gs.load()
        data["groups"].append(create_group("Work", order=1))
        data["groups"].append(create_group("Personal", order=2))
        gs.save(data)

        data = gs.load()
        assert len(data["groups"]) == 3  # General + Work + Personal

        work_group = data["groups"][1]
        assert work_group["name"] == "Work"

        work_group["name"] = "Office"
        gs.save(data)

        data = gs.load()
        assert data["groups"][1]["name"] == "Office"

        data["groups"].pop(1)
        gs.save(data)

        data = gs.load()
        assert len(data["groups"]) == 2
