# Changelog

All notable changes to Nudge are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.2] - 2026-08-28

### Fixed
- **Release packaging** — v2.0.1 tag pointed to an incomplete commit; 2.0.2 ships the full feature set below on `main`.

Includes everything listed in 2.0.1: task search, tray quick-add, debounced saves, pin/hotkey fixes, flat-view boot fix, ghost-frame fix, group search filtering, theme/settings and resize performance improvements.

## [2.0.1] - 2026-08-28

### Added
- **Task search bar** — Ctrl+F opens an inline search bar with scope filters (tasks, groups, tags).
- **Tray quick-add** — add tasks quickly from the system tray context menu.
- **Dim overlay** — subtle backdrop when search or modal flows are active.
- **Debounced persistence** — batches rapid disk writes for tasks, groups, and app state.

### Changed
- **Theme/settings performance** — faster live theme and text-size changes without full UI freezes.
- **Resize performance** — smoother window resizing by deferring per-row text reflow until the drag ends.
- **Task row pooling** — reuses row widgets across renders to reduce startup and re-render cost.

### Fixed
- **Pin to desktop** — survives Win+D / Show Desktop and HWND recreation after layer changes.
- **Global hotkeys** — tray toggle shortcut rebinds correctly after `setWindowFlags`.
- **Flat view boot** — tasks visible immediately when groups are disabled on launch.
- **Startup ghost frames** — no stray window outlines during first paint.
- **Group search** — with groups enabled, search shows only matching tasks inside each group.
- **Single instance** — second launch prints a clear message when Nudge is already running.

## [2.0.0] - 2026-07-02

### Added
- **Clipboard import** — press Ctrl+Shift+V to paste multiple lines of text, each line becomes a separate task.
- **Sound effects** — optional completion sound when tasks are checked off (toggle in Settings → Sound).
- **Stats bar in History** — shows total tasks, today's count, and yesterday's count at the top of the History tab.
- **Card-style task rows in History** — completed tasks display as rounded cards instead of flat rows.
- **Collapse chevrons on History sections** — time period sections (Today, Yesterday, etc.) can now be expanded/collapsed.
- **Ctrl+F to focus tag filter** — quick keyboard shortcut to jump to the tag filter dropdown.
- **Task search** — filter visible tasks in real-time from the title bar.

### Changed
- **History tab sorted most-recent-first** — tasks now appear with the most recent at the top within each time period.
- **Button size reduced in message dialogs** — Quit, Delete, Clear History and other confirmation dialogs use smaller, better-proportioned buttons.
- **Magic numbers replaced with named constants** — 20 UI files cleaned up with centralized spacing, sizing, and margin constants in `src/constants.py`.
- **Bold divider on last high-priority task** — the divider line after the final high-priority task is now bolder for clearer section separation.
- **Priority header removed when all high-priority tasks completed** — the "HIGH PRIORITY" header disappears automatically when no high-priority tasks remain.

### Fixed
- **History count not updating on delete** — deleting tasks from History now correctly updates the section count badge.
- **History tab not updating when task completed while open** — newly completed tasks now appear in History without closing and reopening.
- **Footer task count not updating** — the task count in the footer bar now updates when tasks are added or removed.
- **Button clipping in ThemedMessageDialog** — confirmation dialog buttons no longer get clipped at the bottom edge.
- **Group combo not populating on restart** — the group dropdown now shows all groups immediately on app startup instead of being empty until a new group is created.

## [1.14.0] - 2026-06-29

### Added
- **Flat list priority view** — when groups are disabled, high-priority tasks appear first with a "HIGH PRIORITY" header and a divider separating them from normal tasks. Header and divider use theme accent colors.
- **Drag-and-drop import** — drag text, URLs, or files from any app (Notepad, Chrome, Explorer) onto the task list to create tasks instantly. Files use the filename (no extension) as task text. Multiple items create multiple tasks in order.
- **Drop indicator overlay** — a subtle accent-tinted dashed border overlay appears when dragging external content over the task list, signaling the drop zone.

### Changed
- **History shortcut toggles** — pressing Ctrl+H now closes the history dialog if it's already open, instead of doing nothing.
- **Reminders shortcut configurable** — Alt+R can now be changed in Settings → Shortcuts. Previously it was the only shortcut not wired through the shortcuts tab.
- **Reminders dialog tracked** — pressing Alt+R now toggles the reminders popup (close if open), with proper overlap avoidance via DialogManager.
- **FIX-D1 shortcut suppression narrowed** — shortcut suppression now only applies when the main window's own input bar has focus. Dialog search bars (e.g., History search) no longer block shortcuts.
- **Footer separator restyled** — uses theme border color and updates on theme switch.
- **Footer history button restyled** — visible border using theme colors, slightly larger padding and font for better readability.
- **Footer task count updates on theme switch** — text color now follows the theme's text_muted token.

### Fixed
- **History shortcut not closing dialog** — was suppressed by any QLineEdit focus (including the history dialog's own search bar). Now only suppressed when the main input bar has focus.
- **Reminders dialog not tracked** — pressing Alt+R opened a new dialog every time without closing the existing one. Now tracked in DialogManager with proper toggle behavior.
- **Reminders shortcut save fallback inconsistent** — was `or ""` (empty string), now `or "Alt+R"` matching all other shortcuts.
- **Footer border persisting** — separator and history button borders now properly themed and updatable on theme switch.
- **Footer task count white text in light mode** — label stylesheet now updates with theme text_muted color.

## [1.13.0] - 2026-06-24

### Added
- **Task checkboxes** — each task now has a checkbox to mark it complete. Completed tasks move to History.
- **Due dates** — right-click a task → Set Due Date to add a deadline. Due dates display as colored chips next to the task.
- **Priority indicators** — right-click a task → Set Priority to mark as High priority. High priority tasks show a red indicator.
- **Tags with colors** — right-click a task → Add Tag to organize tasks. Tags appear as colored pills next to the task text. Click a tag pill to change its color with the 8-color palette picker.
- **Recurring tasks** — right-click a task → Set Recurrence to repeat daily, weekly, or monthly. When completed, the task automatically recreates with the next due date.
- **Tag filter dropdown** — filter the task list by specific tags using the dropdown in the title bar. Supports multiple tag selection.
- **Font selection** — choose a custom font for task text in Settings → Appearance.
- **History retention setting** — configure how long to keep history (5 days to Forever) in Settings → Advanced. Older entries are automatically removed on startup.
- **Reminders popup** — press Alt+R to open a popup showing all pending task reminders with cancel options.
- **Footer bar** — shows task count and a shortcut to History for quick access.
- **Tutorial update** — welcome guide now covers checkboxes, due dates, priority, tags, recurring tasks, tag filter, font selection, history retention, and reminders popup.

### Changed
- **History dialog redesigned** — header card with task count badge, search by task text or group name, trash icon button, timestamps on entries, footer with Clear All and Close buttons.
- **Button styles unified** — all buttons (primary, ghost, danger, accent, sidebar, dialog) use consistent 13px font, 500 weight, 8px 20px padding, and 8px border-radius.
- **Overflow menu** — divider added between utility actions and community links. Menu opens from left edge of ··· button.
- **Glass panel drag** — removed deferred move pattern for smoother dragging. Overlap detection only on mouse release.
- **Clear all confirmation** — always shows confirmation dialog with shorter message: "Clear ALL history entries? This cannot be undone."
- **Reset to defaults** — shortened confirmation message: "Reset all settings on this tab to defaults?"
- **Skip confirmation** — shortened to "Skip confirmation" to prevent text clipping.

### Fixed
- **QComboBox dropdown theming** — dropdowns now properly inherit theme colors via QPalette instead of CSS. Styled with monkey-patched showPopup for each combo.
- **Tag filter combo background** — dropdown uses menu background color to match theme.
- **Tag color picker focus loss** — picker now closes when clicking outside the app window using QApplication.focusChanged signal.
- **Crash dialog emoji clipping** — emoji label uses transparent background and fixed height.
- **Crash dialog details toggle** — expand/collapse now resizes dialog instead of relying on sizeHint.
- **Tag filter clear button** — improved styling with red hover state and bold × symbol.
- **Tag filter toggle in Settings** — "Enable tag filter bar" checkbox in Advanced tab to show/hide the filter dropdown.
- **Settings last tab remembered** — Settings dialog opens to the tab you were last on.
- **Tag filter dropdown styling** — uses QPalette for selection colors instead of CSS selection-background-color.
- **Badges clipping at minimum window size** — badges widget uses setMaximumWidth to allow layout compression.
- **Windows notifications** — boot notifications now use winotify with correct app icon instead of QSystemTrayIcon showing Python icon.
- **QComboBox popup QPalette** — popup window now gets QPalette set on each showPopup via monkey-patching.
- **SettingsCardWidget theming** — cards update border and title colors when theme changes.
- **DueDateChip light mode** — chip uses theme text color and updates on theme switch.
- **TaskRowWidget theme refresh** — all task rows update due dates, priority, checkboxes, and countdown labels on theme switch.
- **QFont::setPointSize warning** — changed to setPixelSize in task_group_section and history_row.
- **Glass panel dialog smooth drag** — removed deferred move pattern; direct self.move() in mouseMoveEvent.
- **Footer bar added** — task count label and History shortcut button at bottom of main window.
- **History button moved to footer** — removed from top bar for cleaner layout.
- **Overflow menu divider** — separator between utility and community actions.
- **Tag filter group search** — search bar now matches both task text AND group name.

## [1.12.0] - 2026-06-22

### Added
- **Non-blocking update download** — the download progress dialog no longer freezes the app; you can keep working while the update downloads in the background.
- **Install prompt after download** — when the download finishes, a themed dialog asks "Install Now" or "Remind Me Later" instead of auto-installing.
- **Cached update downloads** — if you click "Remind Me Later", the downloaded file is saved. The next time you check for updates, it skips the download and goes straight to the install prompt.
- **Progress bar improvements** — the progress bar now shows a spinner when the server doesn't report a file size, instead of staying stuck at 0%.

### Fixed
- **Progress bar stuck at 0%** — rewrote the PowerShell download fallback to stream progress via stdout instead of blocking with `-OutFile`.
- **File lock errors on retry** — stale temp files from previous failed downloads are now cleaned up before each new download attempt.
- **PowerShell download timeout** — added retry logic (2 attempts with 2s delay) for the PowerShell fallback path.
- **Progress bar cycling** — progress no longer wraps back to 0% after 100MB when `Content-Length` is missing.

## [1.11.0] - 2026-06-22

### Added
- **Liquid glass aesthetic upgrade** — frosted glass panels now have subtle drop shadows and glow effects on focused inputs.
- **Mouse-following glass shine** — a soft radial glow follows your cursor over the task list, reinforcing the glass metaphor. Toggle in Settings → Appearance.
- **SVG toolbar icons** — Settings and History buttons now use crisp vector icons that match the current theme color.
- **Input glow on focus** — the Add Task bar and shortcut inputs glow with the accent color when active.
- **Live appearance preview** — opacity slider, text size slider, and mouse glow toggle now apply immediately as you adjust them.

### Changed
- **Settings and History buttons** replaced emoji icons (⚙, 🕒) with themed SVG icons.
- **DWM shadow fix** — window corners stay clean without black box edges on first launch.

### Fixed
- **Transparent background** — liquid glass transparency now applies correctly on first launch (not just after a refresh).
- **Text size slider** — changes now apply live to all task rows without needing to click Save.
- **Dev runner** — `dev.py` now handles app crashes gracefully and waits for file changes before restarting.

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
