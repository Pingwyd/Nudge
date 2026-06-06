"""Persist task groups to groups.json (Stage 6)."""

import json
import os
import tempfile
from pathlib import Path

from src.backend.task_groups import default_groups_document, ensure_general_group
from src.backend.paths import get_data_file, migrate_legacy_data


def get_base_dir() -> Path:
    """Backwards-compatible alias — prefer :func:`src.backend.paths.get_data_dir`."""
    from src.backend.paths import get_data_dir
    return get_data_dir()


class GroupStore:
    def __init__(self, filename: str = "groups.json"):
        migrate_legacy_data()
        self.filepath = get_data_file(filename)
        self.data = default_groups_document()

    def load(self) -> dict:
        if not self.filepath.exists():
            self.data = default_groups_document()
            self.save()
            return self.data

        try:
            with open(self.filepath, "r", encoding="utf-8") as handle:
                self.data = json.load(handle)
        except (json.JSONDecodeError, OSError):
            self.data = default_groups_document()

        ensure_general_group(self.data)
        return self.data

    def save(self, data=None) -> None:
        if data is not None:
            self.data = data
        ensure_general_group(self.data)

        directory = self.filepath.parent
        directory.mkdir(parents=True, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".json", text=True)
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=4)
            os.replace(temp_path, self.filepath)
        except Exception:
            os.remove(temp_path)
            raise
