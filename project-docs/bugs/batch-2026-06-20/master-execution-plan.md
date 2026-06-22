# Batch Bug Fix — Master Execution Plan

**Date:** 2026-06-20
**Batch:** batch-2026-06-20
**Bugs:** 7 issues across 7 independent subsystems

---

## Bug Inventory

| ID | Bug | Severity | Confidence | Root cause |
|----|-----|----------|-----------|------------|
| B1 | Update dialog error text clipped | Low | Certain | Missing `adjustSize()` after showing error |
| B2 | Tray icon minimize/restore broken | High | Probable | Platform-specific tray behavior; minimize goes to taskbar not tray |
| B3a | Undo toast clips outside window | Medium | Certain | No bounds checking in `_reposition()` |
| B3b | Undo restore puts task at bottom | Medium | Certain | `restore_task_from_history` appends, no index saved |
| B4 | Shortcut toggle broken (History) | Medium | Certain | `HistoryDialog` doesn't emit `finished` on close |
| B5 | Countdown timer invisible until restart | High | Certain | Reminder setters never notify `TaskRowWidget` |
| B6 | Export uses Qt dialog, not native | Low | Certain | `DontUseNativeDialog` flag forced |

---

## Execution Phases

### Phase 1 — High Severity (S1)
**Goal:** Fix the two high-severity bugs that break core features.
**Bugs:** B2 (tray icon), B5 (countdown timer)
**Dependencies:** None — independent subsystems, can be parallelized.

### Phase 2 — Medium Severity (S2)
**Goal:** Fix the three medium-severity UX/data bugs.
**Bugs:** B3a (toast position), B3b (task restore position), B4 (shortcut toggle)
**Dependencies:** None between these three. B3a and B3b both touch `main_window.py` but different methods.

### Phase 3 — Low Severity (S3)
**Goal:** Fix the two low-severity cosmetic issues.
**Bugs:** B1 (update dialog), B6 (export dialog)
**Dependencies:** None.

---

## Architecture Decisions

### B2 — Tray Icon Platform Independence
**Decision:** Replace `showMinimized()` with `self.hide()` + tray icon show. On Windows, `QSystemTrayIcon` is the cross-platform Qt mechanism — no ctypes needed. The minimize button should hide to tray (not taskbar). Restore should use `showNormal()` + `activateWindow()` + `raise_()`.
**Risk:** `showNormal()` after `hide()` may not restore on all platforms. Fallback: use `setVisible(True)` + `showNormal()`.
**Flagged:** B2 confidence is "probable" — runtime testing needed. If the root cause is different (e.g., tray icon not appearing at all), the fix changes.

### B3a — Toast Positioning Algorithm
**Decision:** Calculate toast geometry relative to parent window. If toast fits at bottom-left inside parent, place there. If it would clip below or to the left of the parent's visible area, place at bottom-right **outside** the parent window (negative x offset from right edge, or use screen coordinates).
**New util:** `_toast_fits_inside_parent()` helper in `UndoToast._reposition()`.

### B3b — Task Position Preservation
**Decision:** Save original index in `_last_archived_task` metadata at archive time. On undo, insert at saved index instead of appending. Handle edge cases: index out of bounds (task was moved by user while archived), group changes.
**Schema change:** Add `_archivedFromIndex` key to the archived task dict (transient, not persisted to history.json — only kept in `_last_archived_task` in memory).

### B4 — Dialog Close Signal
**Decision:** Add `closeEvent` override to `GlassPanelDialog` that calls `self.reject()`, so `finished` is always emitted. This fixes the toggle for HistoryDialog and any future dialogs inheriting GlassPanelDialog.
**Risk:** Low — `reject()` is the standard QDialog close path. SettingsDialog already does this.

### B5 — Countdown Notification
**Decision:** After each reminder setter mutates `task_ref`, look up the `TaskRowWidget` via `self.task_row_widgets[id(task_ref)]` and call `row.set_task_ref(task_ref)`.
**Files touched:** `main_window.py` — `_set_task_reminder`, `_set_task_reminder_at_time`, `_show_custom_reminder_dialog`.

---

## Sprint Decomposition

| Sprint | Phase | Bugs | Est. duration |
|--------|-------|------|--------------|
| S1 | High | B5 (countdown), B2 (tray) | 1-2 days |
| S2 | Medium | B3a (toast), B3b (restore), B4 (toggle) | 1 day |
| S3 | Low | B1 (update dialog), B6 (export dialog) | 0.5 day |

---

## Validation Rule

- **B2 (High):** Mandatory MiMo re-validation after implementation.
- **B5 (High):** Mandatory MiMo re-validation after implementation.
- **B3a, B3b, B4 (Medium):** Re-validation only — all touch `main_window.py` shared code.
- **B1, B6 (Low):** No re-validation needed — isolated, mechanical fixes.
