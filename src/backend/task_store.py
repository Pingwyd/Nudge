import json
import logging
import os
import sys
import threading
import tempfile
from pathlib import Path

from src.backend.logging_config import setup_logging
from src.backend.paths import get_data_file, migrate_legacy_data

setup_logging()
logger = logging.getLogger(__name__)


class TaskStore:
    def __init__(self, filename: str = "tasks.json"):
        migrate_legacy_data()
        self.filepath = get_data_file(filename)
        self.tasks = []
        self._lock = threading.RLock()  # FIX-B2: prevent concurrent load/save races
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
                
            # Ensure directory exists
            dir_name = self.filepath.parent
            dir_name.mkdir(parents=True, exist_ok=True)
                
            # Atomic write: write to a temporary file, then instantly rename it
            temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix='.json', text=True)
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(self.tasks, f, indent=4)
                # Retry on Windows PermissionError (antivirus / indexer lock)
                for attempt in range(3):
                    try:
                        os.replace(temp_path, self.filepath)
                        return
                    except PermissionError:
                        if attempt < 2:
                            import time
                            time.sleep(0.05 * (attempt + 1))
                        else:
                            raise
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                logger.warning("Task save failed: %s", e)
                raise e

    def append_and_save(self, item: dict) -> None:
        """Atomically append an item and persist.  # FIX-B2"""
        with self._lock:
            tasks = self.load()
            tasks.append(item)
            logger.info("Task added: %s", item.get("text", "")[:50])
            self.save()
