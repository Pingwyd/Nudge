# Sprint 1 — High Severity Fixes

**Sprint:** S1
**Phase:** 1 (High Severity)
**Duration:** 1-2 days
**Bugs:** B5 (countdown timer), B2 (tray icon)

---

## Features

### S1-F1: Countdown Timer Visibility
**Bug:** B5 — Countdown labels don't appear until app restart; notifications delayed ~10s
**Root cause:** Reminder setters mutate `task_ref["reminderAt"]` but never call `set_task_ref` on the `TaskRowWidget`

### S1-F2: Tray Icon Platform Fix
**Bug:** B2 — Minimize and maximize from tray icon don't work; needs platform independence
**Root cause:** Probable — minimize button uses `showMinimized()` (taskbar, not tray); restore may fail on some platforms after `hide()`

---

## Chunks

| Chunk | Feature | Model | Type | Depends on |
|-------|---------|-------|------|-----------|
| S1-F1-C1 | Notify TaskRowWidget after reminder set | MiMo V2.5 | Architecture-Reasoning | none |
| S1-F1-C2 | Implement TaskRowWidget notification | DeepSeek V4 Flash | Pure-Logic | S1-F1-C1 |
| S1-F1-C3 | Verify countdown on all 3 setter paths | MiMo V2.5 | Integration-Test | S1-F1-C2 |
| S1-F2-C1 | Diagnose tray restore behavior | MiMo V2.5 | Architecture-Reasoning | none |
| S1-F2-C2 | Fix minimize-to-tray + restore | DeepSeek V4 Flash | Pure-Logic | S1-F2-C1 |
| S1-F2-C3 | Verify tray on Windows | MiMo V2.5 | Integration-Test | S1-F2-C2 |

---

## Sequencing Map

```
S1-F1-C1 ──► S1-F1-C2 ──► S1-F1-C3
                    (sequential within F1)

S1-F2-C1 ──► S1-F2-C2 ──► S1-F2-C3
                    (sequential within F2)

F1 and F2 are INDEPENDENT — can run in parallel.
```

---

## Checkpoint Questions

After S1-F1-C3:
- [ ] Does setting a quick reminder (1 minute) show the countdown label immediately?
- [ ] Does the countdown update every second?
- [ ] Does the notification fire at the correct time?
- [ ] Does the countdown disappear when the reminder fires?

After S1-F2-C3:
- [ ] Does clicking minimize button hide to tray (not taskbar)?
- [ ] Does clicking the tray icon restore the window?
- [ ] Does Ctrl+M toggle hide/show?
- [ ] Does the close (X) button hide to tray?
- [ ] Does "Quit" from tray menu actually quit?
