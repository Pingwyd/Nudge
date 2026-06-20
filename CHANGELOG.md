# Changelog

All notable changes to Nudge are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.10.0] - 2026-06-20

### Added
- **Group drag-reorder** — drag a group's header to rearrange groups. Drop indicator shows between groups. External paste to Notepad etc. copies "Group Name\n- Task 1\n- Task 2".
- **History search** — search bar in History panel filters tasks live as you type.
- **History "Don't ask to delete"** — checkbox to skip the confirmation dialog when clearing history items.
- **Clear All button** in History panel — one-click clear of all archived tasks.
- **Undo toast dismiss button** — small ✕ button to dismiss the undo toast without triggering undo.
- **Horizontal scroll for task input** — longer text scrolls horizontally in the add-task bar and edit field.

### Changed
- **Undo toast width** increased from 350px → 520px to better accommodate longer messages.

### Fixed
- **Group drag not starting** — QPushButton was capturing mouse events before the eventFilter could detect drag motion. Consumed the press event to take control.
- **Group drop indicator invisible** — TaskGroupSection drag handlers now accept `application/x-nudge-group` MIME; indicator raised above layout widgets after render.
- **QLineEdit crash** — removed invalid `setHorizontalScrollBarPolicy()` call on QLineEdit (not a scroll-area widget).

## [1.9.0] - 2026-06-19

### Added
- **Live countdown timer** on tasks with active reminders — shows `Xh Ym`, `Ym`, or `Zs` above the Edit button, updating every second with the accent color from the current theme.
- **Double-click to restore** in History panel — replaces single-click to prevent accidental restores.

### Changed
- **Settings → Reminders** is now its own dedicated tab (between Export and Advanced) instead of a popup dialog.
- **Reset to Defaults** now resets only the active Settings tab (General, Appearance, Shortcuts, Export, Reminders, Advanced, or Help) instead of all settings at once.
- **Undo Toast** is now rendered as a child widget inside the app window instead of a floating top-level window — eliminates positioning glitches and off-screen toasts.

### Fixed
- **Drag stutter** — task rows now use deferred-move with `QTimer.singleShot(0)` coalescing instead of raw `move()` calls, eliminating micro-stutters during drag.
- **Confirmation dialogs** for destructive actions (delete task, delete history item, clear reminder, clear completed) — all now show themed confirmation prompts before proceeding.
- **Entry widget theming** — QKeySequenceEdit, QListWidget, QComboBox, and nested settings panels now properly inherit Dark/Light/OLED themes.

## [1.1.0] - 2026-06-07

### Added
- **Auto-update feature**: Nudge now checks for new releases at startup
  (configurable in Settings → General) and on demand via the ↻ button in
  the title bar. When an update is found, a glass-styled dialog shows the
  version and changelog. "Download & Install" streams the new EXE to
  `%TEMP%\Nudge_update\`, then a PowerShell script replaces the running
  EXE and relaunches Nudge.
- `src/backend/updater.py` — `check_for_update()`, `download_update()`,
  `perform_update()` using stdlib only
- `src/frontend/update_dialog.py` — `UpdateInfoDialog` matching Liquid
  Glass style (frameless, translucent, draggable, overlap detection)
- `checkForUpdates` / `updateCheckUrl` settings persisted in appstate

## [1.0.5] - 2026-06-07

### Fixed
- **ABI mismatch crash that survived v1.0.2 → v1.0.4**: pinned
  `PyQt6==6.6.1` in `requirements.txt` but did not pin **`PyQt6-Qt6`**
  (the package that actually ships the Qt C++ libraries). The resolver
  pulled `PyQt6-Qt6==6.11.1`, so the `PyQt6 6.6.1` Python C extension
  was loading against Qt 6.11 libraries and failing with
  `ImportError: DLL load failed while importing QtCore: The specified
  procedure could not be found`. All previous "fixes" (PATH injection,
  `add_dll_directory`, copying DLLs next to `.pyd` files) addressed
  *loader search path* — they could not fix a symbol-level mismatch
  inside Qt itself.
- `requirements.txt` now pins `PyQt6==6.11.0` and `PyQt6-Qt6==6.11.1`
  as a self-consistent set. Verified working in a clean venv matching
  the CI environment, and the rebuilt EXE launches without the
  PyInstaller crash dialog.

## [1.0.4] - 2026-06-06

### Fixed
- **`DLL load failed while importing QtCore: The specified procedure
  could not be found`** — persisted through v1.0.2–v1.0.3 despite the
  runtime hook. Two root causes:
  1. **`os.environ["PATH"]` is ignored by modern Python (3.8+) on
     Windows** — `LOAD_LIBRARY_SEARCH_DEFAULT_DIRS` is used to load
     `.pyd` files and PATH is not part of the secure DLL set. Replaced
     with `os.add_dll_directory()` which registers the Qt6/bin
     directory AND the bundle root directory via `AddDllDirectory`.
  2. **Qt6 DLLs live in `PyQt6/Qt6/bin/`, `.pyd` files live in
     `PyQt6/`** — these aren't on each other's loader search path.
     The spec now also copies the 11 essential DLLs (`Qt6Core.dll`,
     `Qt6Gui.dll`, `Qt6Widgets.dll`, `Qt6Network.dll`, `Qt6Svg.dll`,
     plus the VC++ runtime) into `_internal/PyQt6/` right next to the
     `.pyd` files, so the OS-level loader finds them naturally.

## [1.0.3] - 2026-06-06

### Fixed
- **`No module named 'PyQt6.sip'` startup crash** (regression on
  PyQt6 6.6.1). The SIP runtime is shipped by the **`pyqt6-sip`**
  PyPI package, not by `PyQt6` itself. `collect_all("PyQt6")` does not
  see it, so the `.pyd` was not bundled. Now `Nudge.spec` calls
  `collect_all("pyqt6-sip")` and `requirements.txt` pins
  `pyqt6-sip==13.11.1` as an explicit dependency.
- **Removed invalid hiddenimports** (`PyQt6.QtGui.QFontMetrics` and
  friends are classes inside `PyQt6.QtGui`, not submodules).
- **Excluded unused Qt subsystems** (Qt3D, QtPdf, QtMultimedia,
  QtPositioning, QtQml, QtQuick, etc.) — slimmer bundle and no more
  "Library not found: Qt63DRender.dll" warnings.

## [1.0.2] - 2026-06-06

### Fixed
- **Startup crash after SmartScreen bypass**: `ImportError: DLL load
  failed while importing QtCore: The specified procedure could not be
  found.` PyQt6's C extension looked for `Qt6Core.dll` and the MSVC
  runtime DLLs via the loader's default search order, which doesn't
  reach the PyInstaller bundle. Added a runtime hook
  (`pyqt6_runtime_hook.py`) that prepends `<bundle>/PyQt6/Qt6/bin` to
  `PATH` and sets `QT_PLUGIN_PATH` / `QT_QPA_PLATFORM_PLUGIN_PATH` so
  Qt and its platform plugin resolve at import time.
- **Bulletproof PyQt6 / winotify bundling**: switched `Nudge.spec` to
  use `collect_all("PyQt6")` and `collect_all("winotify")` so every
  Qt module, plugin, and data file is included.

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
