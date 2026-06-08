"""Prevent multiple Nudge instances via QSharedMemory lock."""

from __future__ import annotations

import os

from PyQt6.QtCore import QSharedMemory


_LOCK_KEY = f"Nudge_Lock_{os.environ.get('USERNAME', 'default')}"


def try_lock() -> bool:
    """Try to acquire the singleton lock.
    
    Returns True if this is the first instance (lock acquired).
    Returns False if another instance is already running.
    """
    mem = QSharedMemory(_LOCK_KEY)
    if mem.attach():
        return False
    if mem.create(1):
        return True
    return False


def release_lock():
    mem = QSharedMemory(_LOCK_KEY)
    if mem.attach():
        mem.detach()
