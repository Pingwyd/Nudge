"""SoundManager — plays task completion sound effects."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.backend.state_manager import StateManager

logger = logging.getLogger(__name__)

_SOUND_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"
_COMPLETION_SOUND = _SOUND_DIR / "task_complete.wav"


class SoundManager:
    """Loads and plays short UI sounds (task completion)."""

    def __init__(self, state_manager: StateManager):
        self._state_manager = state_manager
        self._completion_sound = None
        self._load_completion_sound()

    def _load_completion_sound(self) -> None:
        try:
            from PyQt6.QtMultimedia import QSoundEffect
            from PyQt6.QtCore import QUrl

            if not _COMPLETION_SOUND.exists():
                logger.warning("Completion sound not found: %s", _COMPLETION_SOUND)
                return

            self._completion_sound = QSoundEffect()
            self._completion_sound.setSource(QUrl.fromLocalFile(str(_COMPLETION_SOUND)))
            self._completion_sound.setVolume(0.6)
            logger.debug("Completion sound loaded: %s", _COMPLETION_SOUND)
        except Exception as exc:
            logger.warning("Could not load completion sound: %s", exc)
            self._completion_sound = None

    def play_completion(self) -> None:
        """Play the task completion sound if enabled."""
        if not self._state_manager.state.get("playCompletionSound", True):
            return
        if self._completion_sound is None:
            return
        try:
            self._completion_sound.play()
        except Exception as exc:
            logger.warning("Could not play completion sound: %s", exc)
