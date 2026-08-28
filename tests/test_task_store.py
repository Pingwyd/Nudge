"""Unit tests for TaskStore."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
from src.backend.task_store import TaskStore


@pytest.fixture
def task_store(tmp_path):
    """Create a TaskStore with a temp filepath."""
    filepath = tmp_path / "test_tasks.json"
    with patch("src.backend.task_store.get_data_file", return_value=filepath):
        store = TaskStore("test_tasks.json")
        store.filepath = filepath
        return store


@pytest.fixture
def sample_task():
    """A sample task dictionary."""
    return {
        "id": "task-001",
        "text": "Buy groceries",
        "done": False,
        "createdAt": "2026-06-29T10:00:00",
        "order": 0,
    }


class TestTaskStoreInit:
    """Tests for TaskStore initialization."""

    def test_empty_tasks_list(self, task_store):
        assert task_store.tasks == []


class TestTaskStoreLoad:
    """Tests for TaskStore.load()."""

    def test_load_empty_file(self, task_store):
        result = task_store.load()
        assert result == []

    def test_load_existing_tasks(self, task_store):
        tasks = [{"id": "1", "text": "Task 1"}, {"id": "2", "text": "Task 2"}]
        task_store.filepath.write_text(json.dumps(tasks), encoding="utf-8")
        result = task_store.load()
        assert len(result) == 2
        assert result[0]["text"] == "Task 1"

    def test_load_corrupted_json(self, task_store):
        task_store.filepath.write_text("invalid json{", encoding="utf-8")
        result = task_store.load()
        assert result == []

    def test_load_ensures_schema(self, task_store):
        """Tasks without new fields should get defaults."""
        tasks = [{"id": "1", "text": "Task 1"}]
        task_store.filepath.write_text(json.dumps(tasks), encoding="utf-8")
        result = task_store.load()
        assert result[0]["dueDate"] is None
        assert result[0]["priority"] is None
        assert result[0]["tags"] == []
        assert result[0]["recurrence"] is None


class TestTaskStoreSave:
    """Tests for TaskStore.save()."""

    def test_save_empty_list(self, task_store):
        task_store.save([])
        task_store.flush()
        assert task_store.filepath.exists()
        assert json.loads(task_store.filepath.read_text(encoding="utf-8")) == []

    def test_save_tasks(self, task_store, sample_task):
        task_store.save([sample_task])
        task_store.flush()
        loaded = json.loads(task_store.filepath.read_text(encoding="utf-8"))
        assert len(loaded) == 1
        assert loaded[0]["text"] == "Buy groceries"

    def test_save_is_atomic(self, task_store, sample_task):
        """Verify atomic write doesn't leave temp files."""
        task_store.save([sample_task])
        task_store.flush()
        temp_files = list(task_store.filepath.parent.glob("*.tmp"))
        assert len(temp_files) == 0

    def test_save_updates_instance(self, task_store, sample_task):
        task_store.save([sample_task])
        assert task_store.tasks == [sample_task]


class TestTaskStoreAppendAndSave:
    """Tests for TaskStore.append_and_save()."""

    def test_append_single_task(self, task_store, sample_task):
        task_store.append_and_save(sample_task)
        assert len(task_store.tasks) == 1
        assert task_store.tasks[0]["text"] == "Buy groceries"

    def test_append_multiple_tasks(self, task_store):
        for i in range(3):
            task_store.append_and_save({"id": f"t{i}", "text": f"Task {i}"})
        assert len(task_store.tasks) == 3

    def test_append_persists(self, task_store, sample_task):
        task_store.append_and_save(sample_task)
        # Load in a new TaskStore
        with patch("src.backend.task_store.get_data_file", return_value=task_store.filepath):
            store2 = TaskStore("test_tasks.json")
            store2.filepath = task_store.filepath
            store2.load()
            assert len(store2.tasks) == 1


class TestTaskStoreEnsureSchema:
    """Tests for _ensure_schema method."""

    def test_adds_missing_fields(self, task_store):
        task = {"id": "1", "text": "Task"}
        result = task_store._ensure_schema(task)
        assert result["dueDate"] is None
        assert result["priority"] is None
        assert result["tags"] == []
        assert result["recurrence"] is None

    def test_preserves_existing_fields(self, task_store):
        task = {
            "id": "1",
            "text": "Task",
            "dueDate": "2026-07-01",
            "priority": "high",
            "tags": ["work"],
            "recurrence": {"type": "daily", "interval": 1},
        }
        result = task_store._ensure_schema(task)
        assert result["dueDate"] == "2026-07-01"
        assert result["priority"] == "high"
        assert result["tags"] == ["work"]
        assert result["recurrence"] == {"type": "daily", "interval": 1}
