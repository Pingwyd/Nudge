import json
import logging
import os
import sys
import threading
from pathlib import Path

from src.backend.debounced_saver import DebouncedSaver
from src.backend.logging_config import setup_logging
from src.backend.paths import get_data_file, migrate_legacy_data

setup_logging()
logger = logging.getLogger(__name__)


class TaskStore:
    def __init__(self, filename: str = "tasks.json", delay_ms: int = 200):
        migrate_legacy_data()
        self.filepath = get_data_file(filename)
        self.tasks = []
        self._lock = threading.RLock()  # FIX-B2: prevent concurrent load/save races
        self._saver = DebouncedSaver(self.filepath, delay_ms)
        logger.info("TaskStore initialized: %d tasks", len(self.tasks))

    def _ensure_schema(self, task: dict) -> dict:
        """Ensure task has all required fields with defaults for missing ones."""
        task.setdefault("dueDate", None)
        task.setdefault("priority", None)
        task.setdefault("tags", [])
        task.setdefault("recurrence", None)
        return task

    def load(self):
        with self._lock:  # FIX-B2
            if not self.filepath.exists():
                self.tasks = []
                return self.tasks
            
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
                # Ensure all tasks have the new schema fields
                self.tasks = [self._ensure_schema(task) for task in self.tasks]
            except (json.JSONDecodeError, OSError):
                self.tasks = []
                
            return self.tasks

    def save(self, tasks=None):
        with self._lock:  # FIX-B2
            if tasks is not None:
                self.tasks = tasks
            self._saver.save(self.tasks)

    def flush(self):
        """Immediate write — call on app quit."""
        self._saver.flush()

    def append_and_save(self, item: dict) -> None:
        """Atomically append an item and persist.  # FIX-B2"""
        with self._lock:
            self.tasks.append(item)
            logger.info("Task added: %s", item.get("text", "")[:50])
            self.save()
            self.flush()
