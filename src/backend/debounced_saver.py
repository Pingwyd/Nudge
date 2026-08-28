"""Debounced disk write — batches rapid changes into a single write."""

import copy
import json
import logging
import os
import tempfile
import threading
from pathlib import Path

from PyQt6.QtCore import QTimer, QObject, pyqtSignal


logger = logging.getLogger(__name__)


class DebouncedSaver(QObject):
    """Batches rapid save() calls into a single disk write after a delay."""

    saved = pyqtSignal()

    def __init__(self, filepath: Path, delay_ms: int = 200, parent=None):
        super().__init__(parent)
        self._filepath = filepath
        self._data = None
        self._last_saved = None
        self._lock = threading.Lock()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self._flush)

    def save(self, data):
        """Schedule a debounced write. Skips if data unchanged."""
        with self._lock:
            if data == self._last_saved:
                return
            self._data = data
        if not self._timer.isActive():
            self._timer.start()

    def flush(self):
        """Immediate write — call on app quit or critical state changes."""
        self._timer.stop()
        self._flush()

    def _flush(self):
        """Perform the actual disk write."""
        with self._lock:
            data = self._data
            self._data = None

        if data is None:
            return

        directory = self._filepath.parent
        directory.mkdir(parents=True, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(
            dir=directory, suffix=".json", text=True
        )
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=4)
            for attempt in range(3):
                try:
                    os.replace(temp_path, self._filepath)
                    break
                except PermissionError:
                    if attempt < 2:
                        import time
                        time.sleep(0.05 * (attempt + 1))
                    else:
                        raise
            self._last_saved = copy.deepcopy(data)
            logger.debug("Saved %s", self._filepath.name)
            self.saved.emit()
        except Exception:
            try:
                os.remove(temp_path)
            except OSError:
                pass
            raise
