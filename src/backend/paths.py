"""
Centralized path resolution for Nudge.

All persistent state (settings, tasks, groups, history) lives under the
per-user application data directory so that data survives reinstalls and
upgrades and is never written next to the executable.

Resolution order:
1. Portable mode — if ``portable.flag`` exists next to the EXE, data
   stays alongside it (USB / no-install use case).
2. ``%APPDATA%\\Nudge`` on Windows.
3. ``~/.local/share/Nudge`` on Linux / macOS (fallback).
4. Last-resort temp directory if nothing else is writable.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Iterable

APP_DIR_NAME = "Nudge"
# Previous brand name — used to migrate existing data after a rebrand.
LEGACY_APP_DIR_NAMES: tuple[str, ...] = ("RemindTaskWidget", "Remind")
PORTABLE_FLAG = "portable.flag"
MIGRATED_FLAG = ".migrated_to_appdata"


def _exe_dir() -> Path:
    """Directory containing the running executable (or project root in dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


def _is_portable() -> bool:
    return (_exe_dir() / PORTABLE_FLAG).exists()


def _platform_data_dir() -> Path | None:
    """Return the OS-appropriate per-user data directory, or None if unavailable."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_DIR_NAME
        return None
    # Linux / macOS — XDG-style
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / APP_DIR_NAME


def get_data_dir() -> Path:
    """Return the directory that should hold persistent state files.

    Creates the directory if it does not exist. Falls back to a writable
    temp directory if the preferred location is not usable.
    """
    if _is_portable():
        data_dir = _exe_dir() / "data"
    else:
        preferred = _platform_data_dir()
        data_dir = preferred if preferred is not None else Path(tempfile_gettempdir()) / APP_DIR_NAME

    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        data_dir = Path(tempfile_gettempdir()) / APP_DIR_NAME
        data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


def tempfile_gettempdir() -> str:
    import tempfile
    return tempfile.gettempdir()


def get_data_file(filename: str) -> Path:
    """Return the full path to a state file inside the data directory."""
    return get_data_dir() / filename


def _legacy_filenames() -> Iterable[str]:
    """Files that used to live next to the EXE / project root."""
    return (
        "appstate.json",
        "tasks.json",
        "groups.json",
        "history.json",
    )


def migrate_legacy_data(force: bool = False) -> bool:
    """Copy any pre-AppData state files into the new data directory.

    Also migrates data from a previous AppData folder name (rebrand case).

    Runs once per install. Safe to call on every launch — it bails out
    quickly when there is nothing to do.

    Returns True if any files were migrated, False otherwise.
    """
    data_dir = get_data_dir()
    if _is_portable():
        return False

    marker = data_dir / MIGRATED_FLAG
    if marker.exists() and not force:
        # Still do a one-shot opportunistic copy if a legacy file is newer
        # than its AppData counterpart (e.g. user downgraded then upgraded).
        return _copy_newer_legacy_files(data_dir)

    migrated_any = _migrate_legacy_appdata_dirs(data_dir)
    migrated_any |= _migrate_legacy_exe_dir_files(data_dir)

    # Mark migration done (best-effort).
    try:
        marker.touch(exist_ok=True)
    except OSError:
        pass

    return migrated_any or marker.exists()


def _migrate_legacy_appdata_dirs(data_dir: Path) -> bool:
    """If an old AppData folder exists (rebrand), copy its files into the new one."""
    parent = data_dir.parent
    migrated = False
    for legacy_name in LEGACY_APP_DIR_NAMES:
        if legacy_name == APP_DIR_NAME:
            continue
        legacy_dir = parent / legacy_name
        if not legacy_dir.is_dir():
            continue
        for name in _legacy_filenames():
            src = legacy_dir / name
            dst = data_dir / name
            if not src.exists() or dst.exists():
                continue
            try:
                shutil.copy2(src, dst)
                migrated = True
            except OSError:
                continue
    return migrated


def _migrate_legacy_exe_dir_files(data_dir: Path) -> bool:
    """Copy any pre-AppData state files (next to the EXE) into the new data dir."""
    exe_dir = _exe_dir()
    migrated = False
    for name in _legacy_filenames():
        legacy = exe_dir / name
        target = data_dir / name
        if not legacy.exists() or target.exists():
            continue
        try:
            shutil.copy2(legacy, target)
            migrated = True
        except OSError:
            continue
    return migrated


def _copy_newer_legacy_files(data_dir: Path) -> bool:
    """If a legacy file (in EXE dir or old AppData dir) is newer than the
    AppData copy, prefer the legacy one."""
    copied = False
    sources = [_exe_dir()]
    parent = data_dir.parent
    for legacy_name in LEGACY_APP_DIR_NAMES:
        if legacy_name == APP_DIR_NAME:
            continue
        sources.append(parent / legacy_name)
    for source in sources:
        for name in _legacy_filenames():
            legacy = source / name
            target = data_dir / name
            if not legacy.exists() or not target.exists():
                continue
            try:
                if legacy.stat().st_mtime > target.stat().st_mtime:
                    shutil.copy2(legacy, target)
                    copied = True
            except OSError:
                continue
    return copied
