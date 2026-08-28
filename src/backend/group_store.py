"""Persist task groups to groups.json (Stage 6)."""

import json
import logging
from pathlib import Path

from src.backend.debounced_saver import DebouncedSaver
from src.backend.logging_config import setup_logging
from src.backend.task_groups import default_groups_document, ensure_general_group
from src.backend.paths import get_data_file, migrate_legacy_data

setup_logging()
logger = logging.getLogger(__name__)


class GroupStore:
    def __init__(self, filename: str = "groups.json", delay_ms: int = 200):
        migrate_legacy_data()
        self.filepath = get_data_file(filename)
        self.data = default_groups_document()
        self._saver = DebouncedSaver(self.filepath, delay_ms)
        logger.info("GroupStore initialized: %d groups", len(self.data.get("groups", [])))

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
        self._saver.save(self.data)

    def flush(self) -> None:
        """Immediate write — call on app quit."""
        self._saver.flush()
