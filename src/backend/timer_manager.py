"""Persistent countdown / repeat reminders."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Callable

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.backend.paths import get_data_file


def _now_ts() -> float:
    return time.time()


class TimerConfig:
    def __init__(
        self,
        name: str,
        interval_seconds: int,
        repeat: bool = False,
        timer_id: str | None = None,
        next_trigger_at: float | None = None,
        created_at: float | None = None,
        enabled: bool = True,
    ):
        self.timer_id = timer_id or uuid.uuid4().hex[:12]
        self.name = name
        self.interval_seconds = interval_seconds
        self.repeat = repeat
        self.next_trigger_at = next_trigger_at or (_now_ts() + interval_seconds)
        self.created_at = created_at or _now_ts()
        self.enabled = enabled

    def to_dict(self) -> dict:
        return {
            "timerId": self.timer_id,
            "name": self.name,
            "intervalSeconds": self.interval_seconds,
            "repeat": self.repeat,
            "nextTriggerAt": self.next_trigger_at,
            "createdAt": self.created_at,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, d: dict) -> TimerConfig:
        return cls(
            name=d.get("name", "Reminder"),
            interval_seconds=d.get("intervalSeconds", 300),
            repeat=d.get("repeat", False),
            timer_id=d.get("timerId"),
            next_trigger_at=d.get("nextTriggerAt"),
            created_at=d.get("createdAt"),
            enabled=d.get("enabled", True),
        )


class TimerManager(QObject):
    timer_fired = pyqtSignal(str, str)  # timer_id, name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timers: dict[str, TimerConfig] = {}
        self._qt_timers: dict[str, QTimer] = {}
        self._state_path = get_data_file("appstate.json")

    def load(self, raw_timers: list[dict]) -> None:
        for d in raw_timers:
            cfg = TimerConfig.from_dict(d)
            self._timers[cfg.timer_id] = cfg
            if cfg.enabled:
                self._start_qt_timer(cfg)

    def to_list(self) -> list[dict]:
        return [cfg.to_dict() for cfg in self._timers.values()]

    def add(self, name: str, interval_seconds: int, repeat: bool) -> TimerConfig:
        cfg = TimerConfig(name=name, interval_seconds=interval_seconds, repeat=repeat)
        self._timers[cfg.timer_id] = cfg
        if cfg.enabled:
            self._start_qt_timer(cfg)
        return cfg

    def remove(self, timer_id: str) -> None:
        self._timers.pop(timer_id, None)
        qt = self._qt_timers.pop(timer_id, None)
        if qt is not None:
            qt.stop()

    def set_enabled(self, timer_id: str, enabled: bool) -> None:
        cfg = self._timers.get(timer_id)
        if cfg is None:
            return
        cfg.enabled = enabled
        if enabled:
            cfg.next_trigger_at = _now_ts() + cfg.interval_seconds
            self._start_qt_timer(cfg)
        else:
            qt = self._qt_timers.pop(timer_id, None)
            if qt is not None:
                qt.stop()

    def _start_qt_timer(self, cfg: TimerConfig) -> None:
        old = self._qt_timers.pop(cfg.timer_id, None)
        if old is not None:
            old.stop()
        remaining = max(1, int((cfg.next_trigger_at - _now_ts()) * 1000))
        qt = QTimer(self)
        qt.setSingleShot(not cfg.repeat)
        qt.timeout.connect(lambda tid=cfg.timer_id: self._on_fired(tid))
        qt.start(remaining)
        self._qt_timers[cfg.timer_id] = qt

    def _on_fired(self, timer_id: str) -> None:
        cfg = self._timers.get(timer_id)
        if cfg is None:
            return
        self.timer_fired.emit(timer_id, cfg.name)
        if cfg.repeat:
            cfg.next_trigger_at = _now_ts() + cfg.interval_seconds
            self._start_qt_timer(cfg)
        else:
            cfg.enabled = False
            self._qt_timers.pop(timer_id, None)
