# Sprint 3 — New Features

## Sprint Header

- **Sprint #:** S3
- **Goal:** Add two new features: countdown indicator above Edit button for tasks with reminders, and double-click to restore in History.
- **Depends on:** S2 (all S2 chunks must be complete)
- **Estimated chunks:** 3

---

## Features

### Feature 1: Countdown Indicator Above Edit Button

**User stories / requirements:**
- As a user, if a task has a pending reminder, I should see a countdown timer above the Edit button showing remaining time in `Xh Ym` format.
- The countdown should update every second.
- The countdown should disappear when the reminder fires.
- The countdown should match the theme (accent color text).

**Technical tasks:**
- In `TaskRowWidget.__init__`, detect if the task has a pending reminder (`task.get("reminderAt")` set and `task.get("reminderFired")` is False).
- If so, create a small `QLabel` positioned above or beside the Edit button showing remaining time.
- Add a `QTimer` with 1-second interval to update the countdown.
- Format remaining time as `Xh Ym` (e.g., `1h 23m`, `45m`, `12m 30s`).
- When countdown reaches zero (or task is edited/deleted), stop the timer and hide the label.
- Style the label using theme accent color.
- Add a `set_task_ref(task)` method to TaskRowWidget that sets the task reference and initializes the countdown if needed.
- Ensure only active timers exist (no timer for tasks without reminders).

**Files to modify:**
- `src/frontend/main_window.py` — `TaskRowWidget` class, `render_tasks` or `_append_task_row_widget` to pass task ref

**Tests to write:**
- Manual: add task with 15-minute reminder → countdown shows `15m` above Edit.
- Manual: wait → countdown updates every second.
- Manual: when reminder fires → countdown disappears.
- Manual: task without reminder → no countdown shown.
- Manual: countdown matches Dark/Light/OLED theme.

---

### Feature 2: Double-Click to Restore in History

**User stories / requirements:**
- As a user, I should double-click a history entry to restore it (not single-click).
- Single-click should do nothing (or just select/highlight the row).
- Hover/selection visual feedback should be preserved.

**Technical tasks:**
- In `HistoryEntryLabel` (src/frontend/history_row.py), change `mousePressEvent` to `mouseDoubleClickEvent`.
- Update the tooltip from "Click to restore" to "Double-click to restore".
- In `HistoryDialog.refresh_history` (src/frontend/main_window.py), update the hint label from "Click any entry to restore it" to "Double-click any entry to restore it".
- Verify that single-click still provides visual feedback (hover cursor, selection highlight).

**Files to modify:**
- `src/frontend/history_row.py` — `HistoryEntryLabel.mousePressEvent` → `mouseDoubleClickEvent`
- `src/frontend/main_window.py` — `HistoryDialog.init_ui` hint label text

**Tests to write:**
- Manual: single-click history entry → no restore (just hover/selection feedback).
- Manual: double-click history entry → task restores to main list.
- Manual: hover cursor still shows pointing hand.
- Manual: hint text updated to "Double-click".

---

## Execution Prompts

### CHUNK FILE LIST:
- S3-F1-C1.md — Countdown indicator: add to TaskRowWidget
- S3-F2-C1.md — Double-click restore: change signal in history_row.py

*(2 chunks — both independent, can run in parallel.)*

---

*End of sprint-plan.md*
