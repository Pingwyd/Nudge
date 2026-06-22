# Nudge v1.9 — Master Execution Plan

**Date:** 2026-06-19
**Version Target:** v1.9.0
**Source of Truth:** This file

---

## Scope Summary

Eight features/fixes for v1.9, grouped into three phases by dependency order.

| # | Feature | Priority |
|---|---------|----------|
| 1 | Smoother window drag for History & Settings | High |
| 2 | Undo toast: compact, inside app, overlapping allowed | High |
| 3 | Confirmation dialogs for all destructive actions | High |
| 4 | Reset to Defaults → scoped to active Settings tab only | Medium |
| 5 | Theme fix: entry widgets + keyboard shortcut rebinder + reminders list | Medium |
| 6 | Reminders → own dedicated Settings tab | Medium |
| 7 | Countdown indicator above Edit button (`1h 23m` format) | Medium |
| 8 | Double-click to restore in History (replace single-click) | Medium |

### Phase 4 — History UX, Group Drag, Input Scroll (v1.10)

| # | Feature | Priority |
|---|---------|----------|
| 9 | History "Don't Ask to Delete" checkbox + Clear All button | Medium |
| 10 | History search (live filter) | Medium |
| 11 | Undo toast dismiss button (X) | Low |
| 12 | Group drag-and-reorder + drag group out to text editor | Medium |
| 13 | Input bar horizontal scrolling (add task + edit task) | Low |

---

## Phase 1 — Fix & Polish (no new features, no structural changes)

### Sprint 1.1: Smoother Window Drag

**Problem:** History and Settings dialogs (both `GlassPanelDialog` subclasses) stutter when dragged at high speed. The current drag implementation in `glass_panel_dialog.py:112-120` calls `self.move()` on every `mouseMoveEvent`, which causes frame drops because Qt repaints the entire frameless translucent window on each move.

**Approach:**
- Use `QCursor.setPos()` + `QWidget.move()` with delta batching — only move when the delta exceeds a threshold (e.g., 2px), or use a `QTimer.singleShot(0)` to batch moves into the next event loop iteration.
- Alternative: On Windows, switch to `win32gui.SetWindowPos` via ctypes for smoother movement (bypasses Qt's repaint cycle for frameless windows).
- Add `Qt.WidgetAttribute.WA_DontCreateNativeAncestors` + `setAttribute(WA_NoSystemBackground)` to reduce overdraw during drag.

**Files to modify:**
- `src/frontend/glass_panel_dialog.py` — `mouseMoveEvent`
- `src/frontend/frameless_chrome.py` — verify no conflict with resize handles

**Acceptance criteria:**
- Drag History and Settings windows at fast mouse speeds — no visible stutter.
- Resize handles still work correctly.
- Overlap detection still fires on move.

---

### Sprint 1.2: Undo Toast Fix

**Problem:** The `UndoToast` (main_window.py:379-462) is a frameless `QFrame` with `WindowStaysOnTopHint | Tool` flags. It positions itself at `10, parent.height() - self.height() - 10` which places it at the bottom-left of the parent — but since it's a top-level window (not a child widget), it ends up far from the app window on screen.

**Approach:**
- Convert `UndoToast` from a top-level `QFrame` with window flags to a **child widget** that lives inside the main window's layout (or an overlay `QStackedLayout`). This eliminates the positioning problem entirely.
- Add text wrapping (`setWordWrap(True)`) and constrain max-width so the toast is compact.
- Allow it to overlap the main content (float on top via a `QStackedLayout` or absolute positioning within the parent).
- Match the liquid-glass theme using existing theme tokens.

**Files to modify:**
- `src/frontend/main_window.py` — `UndoToast` class, `_show_undo_toast`, positioning logic

**Acceptance criteria:**
- Toast appears inside the app window boundary (bottom area), not at screen edge.
- Toast wraps long task names instead of stretching.
- Toast visually matches liquid-glass theme.
- Toast overlaps main content area (no gap avoidance).
- Auto-dismisses after 5 seconds. Undo button works.

---

### Sprint 1.3: Confirmation Dialogs for Destructive Actions

**Problem:** Destructive actions (delete task, clear history, clear selected reminders) have no confirmation step.

**Approach:**
- Create a reusable `ConfirmDialog` extending `GlassPanelDialog` (or reuse existing `ThemedMessageDialog` if it already has a Yes/No pattern).
- Wire confirmation into:
  1. Delete task (context menu → "Delete")
  2. Clear history (History dialog → "Clear All")
  3. Clear selected reminders (Settings → Reminders tab → "Clear Selected")
  4. Any other destructive action found during implementation.
- All dialogs must use the app's global theme tokens.

**Files to modify:**
- `src/frontend/main_window.py` — delete task, history clear, reminder clear
- Possibly `src/frontend/themed_message_dialog.py` — verify/enhance existing themed dialog

**Acceptance criteria:**
- Every destructive action shows a themed confirmation dialog before executing.
- "Cancel" aborts the action. "Confirm" proceeds.
- Dialog matches liquid-glass theme in Dark, Light, and OLED modes.

---

## Phase 2 — Settings Restructure

### Sprint 2.1: Reset to Defaults → Scoped to Active Tab

**Problem:** "Reset to Defaults" button calls `_reset_shortcuts_to_defaults()` which only resets shortcuts. The button label implies it resets the current tab's settings, but it's hardcoded to shortcuts.

**Approach:**
- Rename button to "Reset to Defaults" and change its handler to a dispatcher:
  - If General tab is active → reset General checkboxes/sliders to defaults.
  - If Appearance tab is active → reset theme, text size, opacity to defaults.
  - If Shortcuts tab is active → reset all shortcut key sequences to defaults (existing logic).
  - If Export tab is active → reset format, include-history, group filter.
  - If Reminders tab (new) → reset reminder defaults.
- Store default values as a class-level constant dict.
- Each tab gets its own `_reset_tab_to_defaults()` method.

**Files to modify:**
- `src/frontend/main_window.py` — `SettingsDialog._reset_shortcuts_to_defaults`, `init_ui`, new per-tab reset methods

**Acceptance criteria:**
- Clicking "Reset to Defaults" on any tab only resets that tab's values.
- Other tabs' values are untouched.
- Visual feedback (values snap back to defaults).

---

### Sprint 2.2: Reminders → Own Settings Tab

**Problem:** Reminders management (pending task reminders list, clear selected) is currently inside the Advanced tab. It should be its own tab.

**Approach:**
- Extract the "Pending Task Reminders" section from `advanced_tab` into a new `reminders_tab`.
- Add "Reminders" to the sidebar tab list.
- Move the `_task_reminder_list`, `clear_reminder_btn`, and related methods.
- The `_open_reminders_from_settings` button in Help tab should now navigate to the Reminders tab instead of opening a separate dialog (or both — verify user intent).

**Files to modify:**
- `src/frontend/main_window.py` — `SettingsDialog.init_ui`, tab names, sidebar buttons

**Acceptance criteria:**
- Settings sidebar shows: General, Appearance, Shortcuts, Export, Reminders, Advanced, Help.
- Reminders tab shows pending task reminders list + Clear Selected.
- Advanced tab no longer contains reminder list.

---

### Sprint 2.3: Theme Fix for Entry Widgets

**Problem:** Keyboard shortcut rebinder cards (`QKeySequenceEdit` + their `nestedPanel` frame) and the pending task reminders `QListWidget` don't fully respect the current theme (especially OLED).

**Approach:**
- Audit all `QKeySequenceEdit`, `QListWidget`, `QComboBox`, and `QSpinBox` widgets in the Settings dialog.
- Apply theme-aware stylesheets to these widgets using tokens from `get_theme()`.
- Ensure the `nestedPanel` card backgrounds, borders, and text all match the active theme.
- Specifically: the shortcut rebinder box border/background, the reminder list background, and any input-like widgets.

**Files to modify:**
- `src/frontend/main_window.py` — `_apply_theme` or per-widget stylesheet calls
- `src/frontend/theme.py` — potentially add new token generators for `QKeySequenceEdit`, `QListWidget`

**Acceptance criteria:**
- Switch to OLED theme → all entry widgets (shortcut rebinder, reminder list, combo boxes) have OLED-appropriate backgrounds and borders.
- Switch to Light → same widgets have light-appropriate styling.
- No invisible text or invisible borders in any theme.

---

## Phase 3 — New Features

### Sprint 3.1: Countdown Indicator Above Edit Button

**Problem:** No visual countdown showing time remaining until a task's reminder fires.

**Approach:**
- In `TaskRowWidget`, detect if `task.get("reminderAt")` is set and `reminderFired` is false.
- If so, render a small `QLabel` above or beside the Edit button showing remaining time in `Xh Ym` format.
- Start a `QTimer` (1-second interval) on the widget to update the countdown.
- When countdown reaches zero (reminder fires), hide the label.
- Style the countdown label using theme accent color.

**Files to modify:**
- `src/frontend/main_window.py` — `TaskRowWidget` class, add countdown label + timer
- `src/frontend/main_window.py` — `_check_task_reminders` to hide countdown when fired

**Acceptance criteria:**
- Task with a pending reminder shows `1h 23m` (or `45m`, `12m 30s`) above/beside Edit.
- Countdown updates every second.
- Countdown disappears when reminder fires.
- Countdown matches theme (accent color text, subtle styling).
- No performance issue with many tasks having reminders (timer per-widget, but only active ones).

---

### Sprint 3.2: Double-Click to Restore in History

**Problem:** History currently uses single-click to restore a task. User wants double-click instead (to avoid accidental restores).

**Approach:**
- In `HistoryDialog` (or `HistoryEntryLabel`), change the click handler from single-click to double-click.
- Verify the existing `history_row.py` click connection.
- Optionally: single-click could select/highlight the row, double-click restores.

**Files to modify:**
- `src/frontend/history_row.py` — change signal connection
- `src/frontend/main_window.py` — `HistoryDialog` if click is handled there

**Acceptance criteria:**
- Single-click on a history entry does nothing (or selects it).
- Double-click restores the task to the active list.
- Visual feedback on hover/selection is preserved.

---

## Dependency Graph

```
Sprint 1.1 (Drag)      ─── independent
Sprint 1.2 (Undo Toast) ─── independent
Sprint 1.3 (Confirm)    ─── independent
Sprint 2.1 (Reset Scope)─── independent
Sprint 2.2 (Reminders Tab)── depends on 2.1 (reset logic must be tab-aware first)
Sprint 2.3 (Theme Fix)  ─── depends on 2.2 (new tab needs theming)
Sprint 3.1 (Countdown)  ─── depends on 1.3 (reminder UI should be polished before adding countdown)
Sprint 3.2 (Double-Click)── independent
```

**Parallelizable:** 1.1, 1.2, 1.3, 2.1, 3.2 can all run in parallel.
**Sequential chain:** 2.1 → 2.2 → 2.3 → 3.1

---

## Risk Flags

| Risk | Mitigation |
|------|-----------|
| Converting UndoToast from top-level to child widget may break positioning or event handling | Test thoroughly with multi-monitor; ensure toast doesn't interfere with task list scrolling |
| Per-widget countdown timers (1 per task) could cause lag with 75+ tasks | Only create timers for tasks with active reminders; stop timer when reminder fires |
| Window drag smoothness fix on Windows may need ctypes/Win32 — scope creep | Start with Qt-only batching approach; only go to ctypes if Qt approach fails |
| Reset to Defaults per-tab is a large refactor of SettingsDialog | Keep each tab's reset logic self-contained; don't share state between tabs |

---

## Phase 4 — History UX, Group Drag, Input Scroll

### Sprint 4.1: History Delete Confirmation Bypass + Clear All

**Problem:** Users who frequently clean up history are slowed by repetitive confirmation dialogs. Also, there is no "Clear All" button in the History window — only per-entry delete.

**Approach:**
- Add a `QCheckBox` ("Don't ask for confirmation to delete") at the top of `HistoryDialog`, below the hint label.
- Persist the setting in `appstate.json` via `StateManager` (key: `historySkipDeleteConfirm`, default: `False`).
- When checked, `delete_history_item()` skips the `ThemedMessageDialog.question()` call.
- Add a "Clear All" button at the bottom of `HistoryDialog`. When clicked:
  - If checkbox is checked: clear immediately
  - If checkbox is unchecked: show `ThemedMessageDialog.question()` confirmation first
- Clear All removes all entries from `history.json` and clears the UI rows.

**Files to modify:**
- `src/frontend/main_window.py` — `HistoryDialog.init_ui()`, `delete_history_item()`, new `clear_all_history()`
- `src/frontend/theme.py` — style the checkbox to match glass theme

**Acceptance criteria:**
- Checkbox appears at top of History window, persists across sessions.
- When checked, individual delete has no confirmation dialog.
- "Clear All" button visible at bottom of History.
- Clear All respects the checkbox setting.
- All history entries removed on Clear All; UI updates immediately.

---

### Sprint 4.2: History Live Search

**Problem:** Users with many completed tasks can't quickly find a specific entry.

**Approach:**
- Add a `QLineEdit` search bar at the top of `HistoryDialog` (below the checkbox, above the scroll area).
- Connect `textChanged` signal to a filter method that hides/shows `HistoryRowWidget` entries based on whether the task text contains the search query (case-insensitive).
- When the search bar is empty, all entries are shown.
- Style the search bar with a placeholder ("Search history...") and glass-theme styling.

**Files to modify:**
- `src/frontend/main_window.py` — `HistoryDialog.init_ui()`, new `_filter_history()` method

**Acceptance criteria:**
- Search bar appears at top of History window.
- Typing filters history entries in real-time (case-insensitive substring match).
- Empty search shows all entries.
- Search bar styled to match glass theme.

---

### Sprint 4.3: Undo Toast Dismiss Button

**Problem:** Users may want to immediately dismiss the undo toast without waiting for the 5-second timeout, but without performing the undo action.

**Approach:**
- Add an "X" (`QPushButton`) to the right side of the `UndoToast` layout, after the "Undo" button.
- Clicking X calls `_dismiss()` directly (same as timeout — no undo performed).
- Style the X button as a small, subtle close button matching the glass theme.

**Files to modify:**
- `src/frontend/main_window.py` — `UndoToast.__init__()`

**Acceptance criteria:**
- X button appears on the right edge of the undo toast.
- Clicking X dismisses the toast without undoing.
- "Undo" button still works as before.
- Auto-dismiss timeout still works.
- X button styled consistently with glass theme.

---

### Sprint 4.4: Group Drag-and-Reorder + Drag Out to Text Editor

**Problem:** Groups can only be reordered by editing `groups.json` manually. Users want to drag group headers to reorder groups, and drag a group out of the app to paste all its tasks into a text editor.

**Approach:**
- Make `TaskGroupSection.header_btn` draggable (similar to `TaskRowWidget` drag logic).
- Use `QDrag` with `QMimeData`:
  - Internal MIME type: `application/x-nudge-group` — for reordering groups within the app
  - External MIME type: `text/plain` — for dragging out to text editors
  - Plain text format: `"Group Name\n- Task 1\n- Task 2\n..."` (group name as header, tasks bulleted)
- In `MainWindow`, handle `dragEnterEvent`/`dropEvent` for group drops:
  - Internal: reorder `self.groups_data["groups"]` list, re-render
  - External: Qt handles the native drop automatically via `text/plain`
- Add drop indicator (horizontal line) between groups during drag.

**Files to modify:**
- `src/frontend/task_group_section.py` — add drag events to header, MIME data creation
- `src/frontend/main_window.py` — handle group drops in `tasks_widget`, reorder groups_data

**Acceptance criteria:**
- Dragging a group header shows a ghost image of the group header.
- Dropping between groups reorders them in the list and persists to `groups.json`.
- Dragging a group outside the app window and dropping in Notepad/Word inserts the group name and all task texts.
- Drop indicator visible during drag.
- Works with groups enabled; no effect in flat mode.

---

### Sprint 4.5: Input Bar Horizontal Scrolling

**Problem:** Long task text in the add-task input bar or the inline edit field gets clipped or the cursor jumps to the end, making it hard to review before confirming.

**Approach:**
- The `QLineEdit` input bar already supports horizontal scrolling by default when `setMaxLength` is not set and the text exceeds the widget width. Verify this works.
- If not working (e.g., due to stylesheet or size policy overrides), ensure:
  - `QLineEdit.setDragEnabled(True)` — allows text selection and scrolling
  - `QLineEdit.setCursorPosition()` is preserved during edits
  - Horizontal scroll bar policy is not forced off by stylesheets
- For the inline edit `QLineEdit` in `TaskRowWidget`, same verification.
- If horizontal scroll is not natively working, add `QLineEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)`.

**Files to modify:**
- `src/frontend/main_window.py` — `input_bar` setup, `TaskRowWidget.editor` setup (if needed)
- `src/frontend/theme.py` — verify no stylesheet overrides disable horizontal scroll

**Acceptance criteria:**
- Typing long text in the add-task input bar: text scrolls horizontally, cursor stays at the text position.
- Editing a long task: same horizontal scroll behavior.
- No visual glitches or layout jumps.

---

## Dependency Graph (Phase 4)

```
Sprint 4.1 (History Confirm + Clear All) ─── independent
Sprint 4.2 (History Search)              ─── depends on 4.1 (search bar placement above checkbox)
Sprint 4.3 (Toast Dismiss)               ─── independent
Sprint 4.4 (Group Drag)                  ─── independent
Sprint 4.5 (Input Scroll)                ─── independent
```

**Parallelizable:** 4.1, 4.3, 4.4, 4.5 can all run in parallel.
**Sequential:** 4.1 → 4.2

---

## Risk Flags (Phase 4)

| Risk | Mitigation |
|------|-----------|
| Group drag reordering may conflict with existing task drag within groups | Use distinct MIME types (`application/x-nudge-group` vs `application/x-nudge-task-row`) |
| History search filter may be slow with 1000+ entries | Use simple string `in` check (O(n) per keystroke); debounce if needed |
| Horizontal scroll on QLineEdit may be fighting existing stylesheets | Audit theme.py QLineEdit styles for `overflow` or `max-width` overrides |
| Clear All with large history may cause UI freeze | Batch removal in single `tasks_layout` update, call `processEvents()` |

---

## Version Bump

- Update `__version__` in `src/__init__.py` from `"1.9.0"` to `"1.10.0"`.
- Add new section to `CHANGELOG.md`.

---

## Phase 5 — UI Polish & New Features (v1.11)

| # | Feature | Priority | Touches Existing Code |
|---|---------|----------|----------------------|
| 14 | Reminders Drawer (prototype) | High | Yes |
| 15 | Double-Click Ambiguity (tooltips + feedback) | Medium | Yes |
| 16 | Settings Modernization (icons, grid-cards, toggles) | Medium | Yes |
| 17 | History Chronological Headers + Group Badges | Medium | Yes |
| 18 | Liquid Glass Aesthetic Upgrade | Medium | Yes |
| 19 | Information Density (Visual Cards) | Low | Yes |
| 20 | Crash Report Client | Low | Yes |
| 21 | Hover Glow Animation | Low | Yes |

### Sprint 5: Reminders Drawer (Prototype)

**Problem:** Users want the Reminders list to feel like part of the main app, not a separate floating window or a buried Settings tab. A sliding drawer provides a cohesive, app-integrated feel.

**Approach:**
- Create a `DrawerWidget` that slides out from the left side of the main window
- The drawer overlays the task list (pushes content or floats on top)
- Shows pending reminders with task name, countdown, and cancel button
- Animated slide-in/slide-out using `QPropertyAnimation` on `maximumWidth`
- Drawer opens via a button in the chrome bar (toolbar)
- Drawer state persisted (open/closed) across sessions

**Files to modify:**
- `src/frontend/main_window.py` — new `DrawerWidget` class, chrome bar button, animation logic
- `src/frontend/theme.py` — drawer styling for Dark/Light/OLED

**Acceptance criteria:**
- Drawer slides in from left with smooth animation
- Shows all pending reminders with task name and countdown
- Cancel button removes reminder from TimerManager
- Drawer does NOT replace Settings Reminders tab (both exist for now)
- Drawer state (open/closed) persists across sessions
- Works in Dark, Light, and OLED themes

---

### Sprint 6: Double-Click Ambiguity (Tooltips + Feedback)

**Problem:** Double-clicking a task toggles it as "done" (main window) or restores it (history), but there's no visual indicator that double-clicking does anything. Users only look for checkboxes.

**Approach:**
- Add tooltip on task hover in main window: "Double-click to complete"
- Add tooltip on task hover in history: "Double-click to restore"
- Add subtle visual feedback on double-click: brief flash/highlight animation on the row
- Use `QToolTip` or custom tooltip styling for glass theme consistency

**Files to modify:**
- `src/frontend/main_window.py` — `TaskRowWidget` tooltip + flash animation
- `src/frontend/history_row.py` — tooltip + flash animation

**Acceptance criteria:**
- Hovering over a task in main window shows "Double-click to complete" tooltip
- Hovering over a task in history shows "Double-click to restore" tooltip
- Double-clicking a task produces a brief visual flash/highlight (200-300ms)
- Tooltip matches glass theme styling
- No performance impact with many tasks

---

### Sprint 7: Settings Modernization

**Problem:** Settings sidebar lacks visual appeal. Theme selection is plain text. Toggle switches are default OS style.

**Approach:**
- Add icons to sidebar navigation items (General, Appearance, Shortcuts, Export, Reminders, Advanced, Help)
- Create grid-card layout for theme selection (Dark, Light, OLED as visual cards with preview)
- Implement iOS-style toggle switches for boolean settings
- Keep existing shortcut recorder (already implemented)

**Files to modify:**
- `src/frontend/main_window.py` — `SettingsDialog` sidebar, theme grid, toggle widgets
- `src/frontend/theme.py` — toggle switch styling, grid-card styling, icon colors

**Acceptance criteria:**
- Sidebar shows icon + text for each settings tab
- Theme selection displays as visual grid-cards with preview
- Boolean settings use iOS-style toggle switches
- All new widgets respect Dark/Light/OLED themes
- Shortcut recorder still works as before

---

### Sprint 8: History Chronological Headers + Group Badges

**Problem:** History list is a flat list of completed tasks. Users can't quickly find tasks from a specific day or group.

**Approach:**
- Group completed tasks under collapsible chronological headers (Today, Yesterday, This Week, Older)
- Render colorful group badges instead of bracketed text `[Group]` — use group color from groups.json
- Headers are collapsible (click to expand/collapse)
- Keep existing search and "Don't Ask" checkbox from Sprints 4.1–4.2

**Files to modify:**
- `src/frontend/main_window.py` — `HistoryDialog` grouping logic, header widgets
- `src/frontend/history_row.py` — badge rendering

**Acceptance criteria:**
- Tasks grouped under Today, Yesterday, This Week, Older headers
- Headers are collapsible (click toggles visibility)
- Group badges show group name with group color background
- Existing search still filters across all groups
- "Clear All" still clears all entries regardless of group

---

### Sprint 9: Liquid Glass Aesthetic Upgrade

**Problem:** Current theme styling is functional but lacks premium feel. No glows, shadows, or dynamic icons.

**Approach:**
- Add subtle glow effects on focused inputs and buttons
- Add premium drop shadows on dialogs and cards
- Create programmatic SVG icons that adjust color per theme (light/dark/OLED)
- Icons: settings gear, history clock, search magnifier, close X, chevron arrows
- Cache rendered icons for performance

**Files to modify:**
- `src/frontend/theme.py` — glow/shadow styles, SVG icon generators
- `src/frontend/main_window.py` — apply new icons to toolbar buttons

**Acceptance criteria:**
- Focused inputs show subtle glow effect
- Dialogs/cards have drop shadows
- SVG icons adjust color when switching themes
- Icons are crisp at all sizes (16px, 24px, 32px)
- No startup performance regression (icons cached)

---

### Sprint 10: Information Density (Visual Cards)

**Problem:** General Settings tab is a long list of checkboxes without visual grouping. Hard to scan.

**Approach:**
- Group General tab settings into visual cards:
  - **Startup & System:** Run on Startup, Check for Updates
  - **Window Behavior:** Lock Position, Pin, Always on Top
- Cards have subtle border, background, and header
- Use card component from Sprint 7 (Settings Modernization)

**Files to modify:**
- `src/frontend/main_window.py` — `SettingsDialog` General tab layout

**Acceptance criteria:**
- General tab shows grouped visual cards
- Each card has a header and relevant settings
- Cards match glass theme styling
- Settings values still persist correctly

---

### Sprint 11: Crash Report Client

**Problem:** Crash dialog shows raw stack trace. Not user-friendly.

**Approach:**
- Redesign crash_dialog.py with empathetic error screen
- Collapse raw stack trace into "Technical Details" expandable drawer
- Add "Restart" button (relaunches app)
- Add "Send Report" button (copies crash details to clipboard or saves to file)
- Show friendly error message, not technical jargon

**Files to modify:**
- `src/frontend/crash_dialog.py` — full redesign

**Acceptance criteria:**
- Crash screen shows friendly error message
- Technical Details drawer expands to show stack trace
- "Restart" button relaunches the application
- "Send Report" button copies crash details to clipboard
- Dialog matches glass theme in all modes

---

### Sprint 12: Hover Glow Animation

**Problem:** Main panel lacks interactive visual feedback. No sense of "glass" material.

**Approach:**
- Add "Glass Shine" animation that follows mouse cursor on main panel
- Subtle radial gradient or glow effect that moves with cursor
- Effect is subtle — reinforces glass metaphor without being distracting
- Use `QGraphicsEffect` or custom `paintEvent` overlay

**Files to modify:**
- `src/frontend/main_window.py` — main panel hover effect
- `src/frontend/theme.py` — glow effect parameters per theme

**Acceptance criteria:**
- Subtle glow follows cursor on main panel
- Effect is visible in Dark and OLED themes (less visible in Light)
- No performance impact with smooth cursor tracking
- Effect disabled if user has reduced motion preference (if detectable)

---

## Dependency Graph (Phase 5)

```
S5  (Drawer)         ─── independent
S6  (Double-Click)   ─── independent
S7  (Settings Mod)   ─── independent
S8  (History Headers)─── independent
S9  (Liquid Glass)   ─── depends on S7 (icons/toggles need new theme tokens)
S10 (Info Density)   ─── depends on S7 (visual cards use same card component)
S11 (Crash Report)   ─── independent
S12 (Hover Glow)     ─── depends on S9 (glow uses new theme tokens)
```

**Parallelizable:** S5, S6, S7, S8, S11 can all run in parallel.
**Sequential:** S7 → S9 → S12, S7 → S10

---

## Risk Flags (Phase 5)

| Risk | Mitigation |
|------|-----------|
| Drawer may conflict with existing Settings Reminders tab | Build as separate widget; don't remove Settings tab until confirmed |
| Liquid Glass SVG icons may impact startup performance | Cache rendered icons; lazy-load on first theme apply |
| Chronological headers require date parsing of completedAt | Use `datetime.fromisoformat()` (already imported) |
| Crash report client needs actual crash data collection | Use `traceback.format_exception()` + sys info gathering |
| Hover glow may cause lag on low-end GPUs | Make effect optional; disable if frame rate drops |
| iOS-style toggles may not match native feel on Windows | Use custom QPainter rendering for consistent cross-platform look |

---

*End of master-execution-plan.md*
