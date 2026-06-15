# Nudge .NET Rewrite — Master Execution Plan

## Architecture
- **Framework:** .NET 8+ WPF (Windows-only)
- **Pattern:** MVVM
- **Storage:** JSON files in `%APPDATA%\Nudge\` (same format as Python version)
- **Persistence files:** `tasks.json`, `history.json`, `groups.json`, `appstate.json`

---

## Phase 1 — Core Foundation (Ship a working app)

| # | Feature | Python source | .NET equivalent | Priority |
|---|---------|--------------|-----------------|----------|
| 1 | **Frameless window + resize + drag** | `main_window.py`, `frameless_chrome.py` | WPF `WindowStyle=None`, `ResizeMode=CanResizeWithGrip`, custom `WindowChrome` | **P0** |
| 2 | **Task CRUD** (add, edit text, delete, toggle complete, archive to history) | `TaskRowWidget`, `process_input()`, `toggle_task()`, `delete_task()`, `archive_task()` | WPF ListBox + ObservableCollection\<Task\> + inline editing | **P0** |
| 3 | **Persistence** (tasks.json, history.json, groups.json, appstate.json) | `task_store.py`, `group_store.py`, `state_manager.py`, `paths.py` | `System.Text.Json` read/write to `%APPDATA%\Nudge\` | **P0** |
| 4 | **State manager** with defaults + screen clamping | `state_manager.py` (25 default keys) | `appsettings.json` with `IOptions<T>` pattern | **P0** |
| 5 | **Multi-task text input** (split by periods) | `input_parser.py` | Same logic in C# string split | **P0** |
| 6 | **Resize + viewport sync** (Edit button on right) | `_sync_task_list_viewport_width()`, `responsive_text.py` | WPF Grid columns with `*` sizing | **P0** |

---

## Phase 2 — Task Groups & Reordering

| # | Feature | Python source | .NET equivalent | Priority |
|---|---------|--------------|-----------------|----------|
| 7 | **Group CRUD** (create, rename, delete, reorder) | `group_store.py`, `_add_group_dialog()`, `_rename_group()`, `_delete_group()`, `_move_group_order()` | ObservableCollection\<Group\> with property change | **P1** |
| 8 | **Group sections** (collapsible with chevron + count) | `task_group_section.py` | Expander with header template | **P1** |
| 9 | **Group selector** (combo + add button) | `_refresh_group_combo()` | ComboBox + button | **P1** |
| 10 | **Drag-reorder** (flat list + within groups + between groups) | `_on_flat_list_drop()`, `_on_row_dropped()`, `TaskRowWidget` drag | WPF ListBox drag-adorners or `GongSolutions.Wpf.DragDrop` | **P1** |
| 11 | **Drop indicator** (thin line at insertion point) | `_flat_drop_indicator` | Adorner layer | **P1** |

---

## Phase 3 — Context Menus & Dialogs

| # | Feature | Python source | .NET equivalent | Priority |
|---|---------|--------------|-----------------|----------|
| 12 | **Task context menu** (Edit, Copy, Move Up/Down, Move to Top/Bottom, Move to Group, Delete) | `show_task_context_menu()` | `ContextMenu` on each ListBoxItem | **P2** |
| 13 | **Main window context menu** (Settings, AoT, Pin, Clear Completed, Exit) | MainWindow `contextMenuEvent()` | `ContextMenu` on window | **P2** |
| 14 | **Settings dialog** (5 tabs: General, Appearance, Shortcuts, Export, Advanced) | `SettingsDialog` | WPF TabControl in a separate Window | **P2** |
| 15 | **History dialog** (restore/delete from archived) | `HistoryDialog`, `history_row.py` | Separate Window with ListBox | **P2** |
| 16 | **Export dialog** (format picker, group filter, file save) | `export_dialog.py` | Separate Window with WPF SaveFileDialog | **P2** |
| 17 | **Themed message dialog** (Yes/No, OK, Warning) | `themed_message_dialog.py` | Custom WPF window with same buttons | **P2** |

---

## Phase 4 — System Integration

| # | Feature | Python source | .NET equivalent | Priority |
|---|---------|--------------|-----------------|----------|
| 18 | **System tray** (minimize to tray, context menu) | `system_tray.py`, `closeEvent()` | `NotifyIcon` from `System.Windows.Forms` or `Hardcodet.NotifyIcon` | **P3** |
| 19 | **Single-instance guard** | `single_instance.py` | `Mutex` with `EventWaitHandle` to signal existing instance | **P3** |
| 20 | **Run on startup** (Windows Registry) | `_set_run_on_startup_windows()` | Registry via `Microsoft.Win32.Registry` at `CurrentVersion\Run` | **P3** |
| 21 | **Crash reporter** (global exception handler + email) | `crash_reporter.py`, `crash_dialog.py` | `AppDomain.CurrentDomain.UnhandledException` + email | **P3** |
| 22 | **Data directory resolution** (portable flag, AppData) | `paths.py` | `Environment.GetFolderPath(SpecialFolder.ApplicationData)` | **P3** |
| 23 | **Pin to Desktop** (SetWindowPos HWND_BOTTOM) | `desktop_pin.py` | `[DllImport("user32.dll")] SetWindowPos` P/Invoke | **P3** |
| 24 | **Always on Top** toggle | `window_layer.py` | `Topmost = true` on WPF Window | **P3** |
| 25 | **Position lock** (prevent dragging) | `positionLocked` state | Conditional in Window drag handler | **P3** |

---

## Phase 5 — Update System

| # | Feature | Python source | .NET equivalent | Priority |
|---|---------|--------------|-----------------|----------|
| 26 | **Update check** (GitHub Releases API) | `updater.py` | `HttpClient` to GitHub API, semver comparison | **P4** |
| 27 | **Update info dialog** (version, changelog, download) | `update_dialog.py` (`UpdateInfoDialog`) | WPF Window with WebView2 or formatted text | **P4** |
| 28 | **Download with progress** | `update_dialog.py` (`DownloadDialog`) | `HttpClient.GetAsync` with `HttpCompletionOption.ResponseHeadersRead` | **P4** |
| 29 | **Install & restart** (download .exe, spawn, quit) | `_spawn_installer()` | Download to temp, `Process.Start` new exe, `Application.Current.Shutdown()` | **P4** |

---

## Phase 6 — Advanced Features

| # | Feature | Python source | .NET equivalent | Priority |
|---|---------|--------------|-----------------|----------|
| 30 | **Timers / Reminders** (interval countdown with tray notification) | `timer_manager.py`, `TimerDialog` | `System.Threading.Timer` + `NotifyIcon.ShowBalloonTip()` | **P5** |
| 31 | **Global hotkeys** (show/hide from anywhere) | `GlobalHotkeyFilter` (Win32 RegisterHotKey) | `RegisterHotKey` P/Invoke or `NHotkey` library | **P5** |
| 32 | **Configurable shortcuts** (6 shortcuts, saved in state) | `update_keyboard_shortcuts()` | `KeyBinding` with saved `KeyGesture` | **P5** |
| 33 | **Double-escape to quit** | `_on_escape_pressed()` | `PreviewKeyDown` handler with counter + timer | **P5** |

---

## Phase 7 — Visual Polish

| # | Feature | Python source | .NET equivalent | Priority |
|---|---------|--------------|-----------------|----------|
| 34 | **Theme system** (Dark + Light, full token set ~26 colors) | `theme.py` (766 lines, 18 stylesheet builders) | WPF `ResourceDictionary` merged dictionaries per theme | **P6** |
| 35 | **Liquid glass look** (translucent background, blur) | `WA_TranslucentBackground` + `glassPanel` styles | `Window.AllowsTransparency=True` + `SystemDropShadowChrome` or `WindowChrome` + acrylic brush | **P6** |
| 36 | **Overlap opacity** (solid bg when overlapping another dialog) | `_update_overlap_opacity()` | Check window intersection, swap background | **P6** |
| 37 | **Fade in/out animations** | `animation_helper.py` | WPF `DoubleAnimation` on `Opacity` | **P6** |
| 38 | **Dialog placement** (avoid overlapping main window) | `_place_dialog_avoiding_rects()` | Calculate screen-relative position with candidate positions | **P6** |

---

## Phase 8 — Support & Polish

| # | Feature | Python source | .NET equivalent | Priority |
|---|---------|--------------|-----------------|----------|
| 39 | **Feedback dialog** (text input + app state → Gmail) | `feedback_dialog.py` | WPF Window, clipboard copy, process start mailto | **P7** |
| 40 | **Support dialog** (donate button) | `support_dialog.py` | WPF Window with `Process.Start` to Flutterwave URL | **P7** |
| 41 | **What's New dialog** (changelog after update) | `whats_new_dialog.py` | WPF Window, read from embedded changelog | **P7** |
| 42 | **Tutorial dialog** (first-launch feature guide) | `TutorialDialog` | WPF Window with scrollable feature list | **P7** |
| 43 | **Boot checker** (notify old incomplete tasks) | `boot_checker.py` | Tray notification on startup | **P7** |
| 44 | **Export service** (TXT, MD, CSV) | `export_service.py` | C# string builders per format | **P7** |
| 45 | **Icon set** (window, tray, .ico resource) | `icon.py` | Embedded `.ico` resource | **P7** |

---

## Execution Order Summary

```
Phase 1: Core Foundation     → working app with tasks + persistence (P0)
Phase 2: Groups & Reorder    → groups + drag-drop (P1)
Phase 3: Dialogs             → settings, history, export, context menus (P2)
Phase 4: System Integration  → tray, single-instance, startup, crash (P3)
Phase 5: Auto-Update         → update check, download, install (P4)
Phase 6: Advanced Features   → timers, hotkeys, shortcuts (P5)
Phase 7: Visual Polish       → themes, glass, animations, placement (P6)
Phase 8: Support & Polish    → feedback, donate, changelog, export (P7)
```
