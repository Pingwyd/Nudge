"""Prevent multiple Nudge instances via QSharedMemory lock."""

from __future__ import annotations

import os
import atexit

from PyQt6.QtCore import QSharedMemory


_LOCK_KEY = f"Nudge_Lock_{os.environ.get('USERNAME', 'default')}"
_lock: QSharedMemory | None = None


def try_lock() -> bool:
    """Try to acquire the singleton lock.
    
    Returns True if this is the first instance (lock acquired and held
    for the lifetime of the process). Returns False if another instance
    is already running.
    """
    global _lock
    mem = QSharedMemory(_LOCK_KEY)
    if mem.create(1):
        _lock = mem
        atexit.register(_release)
        return True
    return False


def _release():
    global _lock
    if _lock is not None:
        _lock.detach()
        _lock = None
