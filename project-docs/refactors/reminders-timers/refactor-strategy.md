# Refactor Strategy: Reminders & Timers Consolidation

**Area:** Reminders & Timers Feature
**Date:** 2026-06-20
**Status:** PENDING APPROVAL

---

## Step 1 — Smell Catalogue & Analysis

### 1.1 Architectural Split (Critical)

Two completely independent systems for time-based notifications:

| System | Engine | Persistence | Precision | Lifecycle |
|--------|--------|-------------|-----------|-----------|
| Task Reminders | 15s polling (`_check_task_reminders`) | `tasks.json` fields (`reminderAt`, `reminderFired`, `reminderRepeat`) | ±15 seconds | Fragile — no cleanup on archive/delete |
| Generic Timers | Event-driven `QTimer` objects | `appstate.json["timers"]` | Millisecond | Clean — explicit add/remove |

**Root cause:** Task reminders were bolted on as dict fields on task objects, while generic timers got a proper manager class. They evolved independently and were never unified.

### 1.2 Notification Duplication (High)

Both systems call `self._tray.show_message("Nudge", f"Reminder: {name}")` with near-identical logic:
- `_check_task_reminders()` at `main_window.py:3605` — for task reminders
- `_on_timer_fired()` at `main_window.py:3568` — for generic timers

The notification formatting and delivery path are copy-pasted.

### 1.3 Zombie Reminder Fields (High)

`archive_task()` (line 3271) copies the task to history with `reminderAt`/`reminderFired`/`reminderRepeat` fields intact. These fields are never stripped. The polling loop only iterates `self.tasks` (not history), so these reminders silently die. Worse, `restore_task_from_history()` (line 3327) brings back stale `reminderAt` — if the timestamp is in the past, the next 15s poll fires it immediately.

### 1.4 No Cleanup on Delete (Medium)

`delete_task()` (line 3255) removes the task from `self.tasks` and saves. If the task had an active reminder, it's simply abandoned. No notification, no cleanup — the polling loop never sees it again. This is correct behavior (the reminder is gone with the task), but the code path doesn't explicitly handle it.

### 1.5 Triple-Duplicated Tray Cooldown (Medium)

The pattern:
```python
if not getattr(self, '_tray_notified', False):
    self._tray.show_message("Nudge", "Still running in tray...")
    self._tray_notified = True
    QTimer.singleShot(10000, lambda: setattr(self, '_tray_notified', False))
```
is copy-pasted at lines 2029, 2042, and 2199.

### 1.6 SettingsDialog Reminders Tab Inefficiency (Low)

`_populate_task_reminder_list()` (line 1605) iterates all `self.tasks` on every refresh. The tab doesn't auto-refresh — the user must close and reopen the dialog to see changes.

### 1.7 Dead/Unused Code (Low)

- `REMINDER_LIST_TEXT_MAX = 60` in `constants.py` is defined but unused — `_populate_task_reminder_list` uses hardcoded `[:60]` slice.
- `reminderInterval` key in `scripts/mem_test.py` references a non-existent module.
- TimerManager's `_start_qt_timer` (line 112) clamps remaining to `max(remaining, 1)` — if the app was closed longer than the interval, the timer fires instantly on boot (by design, but undocumented).

### 1.8 Timer Persistence Gap (Low)

Timer state is only saved in three places: boot (line 1928), timer fire (line 3569), and Reminders dialog close (line 3580). If the user opens TimerDialog, adds a timer, and crashes before closing, the timer is lost.

---

## Step 2 — Refactoring Strategy

### Guiding Principle

**TimerManager becomes the single source of truth for all time-based notifications.** Task reminders become "task-linked timers" — same engine, same persistence, same UI. The 15s polling loop is eliminated.

### What Changes

| Before | After |
|--------|-------|
| Task reminders stored as dict fields in `tasks.json` | Task reminders stored as `TimerConfig` entries in `appstate.json["timers"]` with `task_id` reference |
| 15s polling loop scans all tasks every 15 seconds | `QTimer` fires at exact due time (event-driven) |
| Two notification code paths | One notification path (`_on_timer_fired`) |
| TimerDialog shows only generic timers | TimerDialog shows all timers (generic + task-linked) |
| SettingsDialog Reminders tab iterates tasks | SettingsDialog Reminders tab reads from TimerManager |
| Reminder fields survive archive/restore (zombie bug) | Reminder fields are removed from task dicts entirely |

### What Stays the Same

- Task dicts keep `reminderAt` as a **derived read-only field** for countdown label display (computed from TimerManager, not persisted on the task)
- The custom reminder dialog (`_show_custom_reminder_dialog`) still works — it just calls `timer_manager.add()` instead of writing dict fields
- Generic timers work exactly as before
- Tray notification delivery (`show_message`) is unchanged

### Data Migration Strategy

On boot, before loading TimerManager:
1. Scan `self.tasks` for any task with `reminderAt` field
2. For each, create a `TimerConfig` with `task_id=task["id"]`
3. Remove `reminderAt`/`reminderFired`/`reminderRepeat` from the task dict
4. Save `tasks.json` (cleaned) and `appstate.json["timers"]` (with new entries)
5. This is a one-time migration — after it runs, no task will have reminder fields

### Notification Debouncing (Deferred)

The user suggested bundling multiple alerts into one notification. I'm **deferring this** to a future iteration because:
- It adds complexity to the notification path
- The current behavior (separate notifications) is functional
- It can be added non-destructively later
- The primary goal of this refactor is consolidation, not UX overhaul

### Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Migration fails → lose reminders | High | Run migration before TimerManager load; log errors; keep original fields as backup until migration confirmed |
| Countdown label breaks | Medium | Test `TaskRowWidget._start_countdown()` with new data source |
| TimerDialog shows stale data | Low | Connect `timer_fired` signal to dialog refresh |
| SettingsDialog Reminders tab breaks | Low | Update `_populate_task_reminder_list` to read from TimerManager |

---

## Step 3 — Chunk Decomposition

### Model Assignments

| Chunk | Description | Type | Assigned Model | Rationale |
|-------|-------------|------|----------------|-----------|
| C1 | Extend TimerConfig with task_id | Mechanical | ⚡ DeepSeek | Add field + serialize — no judgment needed |
| C2 | Add task-reminder methods | Structural | 🧠 MiMo | New API design — needs reasoning about edge cases |
| C3 | Migrate existing reminders | Structural | 🧠 MiMo | Data migration — correctness critical, needs supervision |
| C4 | Replace polling loop | Structural | 🧠 MiMo | Core architectural change — must preserve behavior |
| C5 | Update set/clear UI | Mechanical | ⚡ DeepSeek | Simple replacement — dict writes → method calls |
| C6 | Update SettingsDialog tab | Mechanical | ⚡ DeepSeek | Data source swap — pattern-based |
| C7 | Fix countdown label | Structural | 🧠 MiMo | Changes widget's data source — needs correctness reasoning |
| C8 | Fix archive/delete cancel | Mechanical | ⚡ DeepSeek | Add cancel calls — straightforward |
| C9 | Deduplicate tray cooldown | Mechanical | ⚡ DeepSeek | Extract method — pure mechanical |
| C10 | Cleanup dead code | Mechanical | ⚡ DeepSeek | Remove unused code — no judgment needed |

**Execution rule:** DeepSeek implements mechanical chunks in isolation. MiMo implements or supervises all structural chunks. Every chunk's output is validated by MiMo before proceeding to the next.

Chunks are ordered to minimize breakage: foundation first, then migration, then consolidation, then cleanup.

### C1: Extend TimerConfig with task_id field
**CHANGE TYPE:** Mechanical
**BREAKING RISK:** Low

Add `task_id: str | None = None` to `TimerConfig`. Update serialization (`to_dict` / `from_dict`). No behavior change — existing timers have `task_id=None`.

### C2: Add `get_timer_for_task()` and `add_task_reminder()` to TimerManager
**CHANGE TYPE:** Structural
**BREAKING RISK:** Low

Add two new methods:
- `add_task_reminder(task_id, name, trigger_at, repeat_minutes)` — creates a `TimerConfig` with `task_id` set
- `get_timer_for_task(task_id) -> TimerConfig | None` — lookup by task_id

Also add `cancel_task_reminder(task_id)` for cleanup on delete/archive.

### C3: Migrate existing task reminder fields to TimerManager
**CHANGE TYPE:** Structural
**BREAKING RISK:** Medium

One-time migration at boot:
1. Before `timer_manager.load()`, scan tasks for `reminderAt`
2. Create `TimerConfig` entries via `timer_manager.add_task_reminder()`
3. Strip reminder fields from tasks
4. Save both stores

### C4: Replace `_check_task_reminders` with TimerManager signals
**CHANGE TYPE:** Structural
**BREAKING RISK:** High

- Remove `_task_reminder_timer` (the 15s QTimer)
- Remove `_check_task_reminders()` method
- Extend `_on_timer_fired()` to handle task-linked timers: look up task by `task_id`, get text, fire notification
- For repeating task reminders: reset `next_trigger_at` in TimerManager (already handled by `_on_fired`)

### C5: Update task reminder set/clear UI to use TimerManager
**CHANGE TYPE:** Mechanical
**BREAKING RISK:** Medium

- `_set_task_reminder()` → calls `timer_manager.add_task_reminder()`
- `_set_task_reminder_at_time()` → calls `timer_manager.add_task_reminder()`
- `_clear_task_reminder()` → calls `timer_manager.cancel_task_reminder()`
- `_show_custom_reminder_dialog()` → calls `timer_manager.add_task_reminder()`
- Context menu "Clear Reminder" → calls `timer_manager.cancel_task_reminder()`

### C6: Update SettingsDialog Reminders tab
**CHANGE TYPE:** Mechanical
**BREAKING RISK:** Low

`_populate_task_reminder_list()` iterates `timer_manager.to_list()` filtered for `task_id is not None`, instead of iterating `self.tasks`.

### C7: Fix countdown label to read from TimerManager
**CHANGE TYPE:** Structural
**BREAKING RISK:** Medium

`TaskRowWidget._start_countdown()` currently reads `task.get("reminderAt")`. Change to call `main_window._timer_manager.get_timer_for_task(task_id)` and read `next_trigger_at`.

### C8: Fix archive/delete to cancel task reminders
**CHANGE TYPE:** Mechanical
**BREAKING RISK:** Low

- `archive_task()` → call `timer_manager.cancel_task_reminder(task_id)`
- `delete_task()` → call `timer_manager.cancel_task_reminder(task_id)`
- `restore_task_from_history()` → strip reminder fields (they're now in TimerManager, not on the task)

### C9: Deduplicate tray notification cooldown
**CHANGE TYPE:** Mechanical
**BREAKING RISK:** Low

Extract the triple-repeated tray cooldown pattern into a `_notify_tray_once(title, message)` helper method.

### C10: Cleanup dead code
**CHANGE TYPE:** Mechanical
**BREAKING RISK:** Low

- Remove `REMINDER_LIST_TEXT_MAX` constant (unused)
- Remove `reminderInterval` from `scripts/mem_test.py`
- Remove stale reminder field references in `_populate_task_reminder_list`
- Ensure `tasks.json` is cleaned of reminder fields after migration

---

## Execution Order

```
C1 (TimerConfig.task_id) → C2 (TimerManager methods) → C3 (migration)
    → C4 (replace polling) → C5 (set/clear UI) → C6 (Settings tab)
    → C7 (countdown label) → C8 (archive/delete fix) → C9 (tray dedup)
    → C10 (cleanup)
```

C1–C3 are foundation (no behavior change). C4 is the critical switchover. C5–C8 are UI updates. C9–C10 are cleanup.

---

## Step 4 — Logic-Correctness Validation Checklist

After each structural chunk, verify:

- [ ] Generic timers still fire at correct times
- [ ] Task reminders fire at correct times (not ±15s)
- [ ] Repeating task reminders advance correctly
- [ ] Countdown label shows correct remaining time
- [ ] Clearing a reminder removes it from TimerManager
- [ ] Archiving a task cancels its reminder
- [ ] Restoring a task does NOT restore a stale reminder
- [ ] Deleting a task cancels its reminder
- [ ] SettingsDialog Reminders tab shows correct list
- [ ] TimerDialog shows both generic and task-linked timers
- [ ] Tray notification fires with correct task text
- [ ] appstate.json["timers"] persists correctly
- [ ] tasks.json no longer contains reminder fields after migration
