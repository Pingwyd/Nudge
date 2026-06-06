import json
import os
import sys
import tempfile
from pathlib import Path

from src.backend.paths import get_data_file, migrate_legacy_data


def get_base_dir() -> Path:
    """Backwards-compatible alias — prefer :func:`src.backend.paths.get_data_dir`."""
    from src.backend.paths import get_data_dir
    return get_data_dir()


class TaskStore:
    def __init__(self, filename: str = "tasks.json"):
        migrate_legacy_data()
        self.filepath = get_data_file(filename)
        self.tasks = []

    def load(self):
        if not self.filepath.exists():
            self.tasks = []
            return self.tasks
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.tasks = json.load(f)
        except (json.JSONDecodeError, OSError):
            self.tasks = []
            
        return self.tasks

    def save(self, tasks=None):
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
            os.replace(temp_path, self.filepath)
        except Exception as e:
            os.remove(temp_path)
            raise e
