# Sprint 1 — Fix & Polish

## Sprint Header

- **Sprint #:** S1
- **Goal:** Fix three independent polish issues: smooth window drag, undo toast positioning, and confirmation dialogs for destructive actions.
- **Depends on:** None
- **Estimated chunks:** 6

---

## Features

### Feature 1: Smoother Window Drag (History & Settings)

**User stories / requirements:**
- As a user, dragging the History or Settings window at high speed should feel smooth with no visible stutter.
- Resize handles must continue to work correctly.
- Overlap detection must still fire during move.

**Technical tasks:**
- Modify `GlassPanelDialog.mouseMoveEvent` to reduce repaint overhead during drag.
- Strategy: batch move deltas — only call `self.move()` when the accumulated delta exceeds a threshold (2px), or defer the move to the next event loop iteration via `QTimer.singleShot(0, ...)`.
- Verify `FramelessChromeController` in `frameless_chrome.py` has no conflict (it handles title-bar drag for MainWindow; GlassPanelDialog uses its own drag in `mousePressEvent`/`mouseMoveEvent`).

**Files to modify:**
- `src/frontend/glass_panel_dialog.py` — `mouseMoveEvent`, possibly add `_drag_batch_pos` accumulator

**Tests to write:**
- Manual: drag History/Settings at fast mouse speed, no stutter.
- Manual: resize handles still work.
- Manual: overlap opacity still updates during move.

---

### Feature 2: Undo Toast Fix

**User stories / requirements:**
- As a user, after completing a task, the undo toast should appear inside the main app window, not at the far edge of the screen.
- The toast should wrap long task names and be compact.
- The toast should overlap the main content area (float on top).
- The toast should match the liquid-glass theme.
- Auto-dismiss after 5 seconds. Undo button must work.

**Technical tasks:**
- Convert `UndoToast` from a top-level `QFrame` with `WindowStaysOnTopHint | Tool` flags to a child widget that lives inside the main window.
- Use a `QStackedLayout` or absolute positioning within the main window's central widget to overlay the toast on top of content.
- Add `setWordWrap(True)` and constrain `maxWidth` so the toast is compact.
- Apply theme tokens from `get_theme()` for glass styling.
- Remove `_position_near_parent` (no longer needed — positioning is relative to parent).
- Ensure toast does not interfere with task list scrolling.

**Files to modify:**
- `src/frontend/main_window.py` — `UndoToast` class, `_show_undo_toast`, positioning

**Tests to write:**
- Manual: complete a task → toast appears inside app window boundary.
- Manual: long task name → toast wraps, doesn't stretch to screen edge.
- Manual: toast overlaps task list content.
- Manual: toast matches Dark/Light/OLED themes.
- Manual: Undo button restores the task.
- Manual: toast auto-dismisses after 5 seconds.

---

### Feature 3: Confirmation Dialogs for Destructive Actions

**User stories / requirements:**
- As a user, before any destructive action (delete task, clear history, clear selected reminders), a themed confirmation dialog must appear.
- "Cancel" aborts the action. "Confirm" proceeds.
- The dialog must match the liquid-glass theme in Dark, Light, and OLED modes.

**Technical tasks:**
- Audit existing `ThemedMessageDialog` — it already has `question()` static method that returns bool. Verify it uses `GlassPanelDialog` and matches theme.
- Wire `ThemedMessageDialog.question()` into:
  1. Delete task (context menu → "Delete" in `show_task_context_menu`)
  2. Clear history (History dialog → clear all button)
  3. Clear selected reminders (Settings → Advanced → "Clear Selected")
- If any destructive action is missing confirmation, add it.

**Files to modify:**
- `src/frontend/main_window.py` — delete task handler, history clear handler, reminder clear handler

**Tests to write:**
- Manual: delete task → confirmation appears → Cancel aborts, Confirm deletes.
- Manual: clear history → confirmation appears → Cancel aborts, Confirm clears.
- Manual: clear selected reminders → confirmation appears → Cancel aborts, Confirm clears.
- Manual: all three dialogs match active theme (Dark, Light, OLED).

---

## Execution Prompts

### CHUNK FILE LIST:
- S1-F1-C1.md — Smooth drag: architecture analysis
- S1-F1-C2.md — Smooth drag: implement batch move
- S1-F2-C1.md — Undo toast: convert to child widget
- S1-F3-C1.md — Confirmation dialogs: wire ThemedMessageDialog into destructive actions

*(4 chunks total — S1-F1 is split into analysis + implementation because the drag fix requires reasoning about Qt's repaint cycle and Win32 interaction before writing code.)*

---

*End of sprint-plan.md*
