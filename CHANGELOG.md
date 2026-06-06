# Changelog

All notable changes to Nudge are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-06-06

### Fixed
- **Startup crash on first launch**: `ModuleNotFoundError: No module named 'PyQt6.sip'`.
  PyInstaller's static analysis does not pick up the SIP runtime, so the
  generated `PyQt6` bindings failed to import at startup. Added
  `PyQt6.sip` (and the other commonly missed `PyQt6.Qt*` submodules) to
  `Nudge.spec` `hiddenimports`.

## [1.0.0] - 2026-06-06

### Added
- First public release.
- Liquid-glass task widget with frosted acrylic panels and dark / light themes.
- Task list with inline add, edit, delete, reordering, and groups.
- Persistent state under `%APPDATA%\Nudge\` (with portable mode).
- Settings dialog: theme, task text size, window opacity, keyboard shortcuts,
  start-on-boot, always-on-top, pinned-to-desktop, position lock, export.
- History panel for completed / archived tasks with restore.
- Export to `.txt`, `.md`, and `.csv`, with or without history.
- Windows toast notification on boot for tasks created before today.
- Keyboard shortcuts: `Ctrl+H` (history), `Ctrl+,` (settings),
  `Ctrl+P` (pin/unpin), `Alt+T` (always-on-top), `Ctrl+E` (export).
- CI/CD pipeline: tagged releases publish a zipped Windows build and a
  signed Inno Setup installer to GitHub Releases.
