# Refactor Checklist: Reminders & Timers Consolidation

**Area:** Reminders & Timers
**Strategy:** `refactor-strategy.md`
**Status:** PENDING APPROVAL — no code changes until approved

---

## Chunk Status

| Chunk | Description | Type | Risk | Model | Status |
|-------|-------------|------|------|-------|--------|
| C1 | Extend TimerConfig with task_id | Mechanical | Low | ⚡ DeepSeek | **Done** |
| C2 | Add task-reminder methods to TimerManager | Structural | Low | 🧠 MiMo | **Done** |
| C3 | Migrate existing task reminders to TimerManager | Structural | Medium | 🧠 MiMo | **Done** |
| C4 | Replace polling loop with TimerManager signals | Structural | High | 🧠 MiMo | **Done** |
| C5 | Update set/clear UI to use TimerManager | Mechanical | Medium | ⚡ DeepSeek | **Done** |
| C6 | Update SettingsDialog Reminders tab | Mechanical | Low | ⚡ DeepSeek | **Done** |
| C7 | Fix countdown label to read from TimerManager | Structural | Medium | 🧠 MiMo | **Done** |
| C8 | Fix archive/delete to cancel task reminders | Mechanical | Low | ⚡ DeepSeek | **Done** |
| C9 | Deduplicate tray notification cooldown | Mechanical | Low | ⚡ DeepSeek | **Done** |
| C10 | Cleanup dead code | Mechanical | Low | ⚡ DeepSeek | **Done** |

## Dependency Graph

```
C1 ──→ C2 ──→ C3 ──→ C4 ──→ C5 ──→ C10
              │       │
              │       ├──→ C7
              │       │
              └──→ C6  │
                       │
              C2 ──→ C8 │
                       │
C9 (independent) ──────┘
```

## Verification After Each Chunk

- [ ] All 9 syntax checks pass (`python -m py_compile` on all changed files)
- [ ] Generic timers still fire correctly
- [ ] Task reminders fire at correct times
- [ ] Countdown label shows correct remaining time
- [ ] SettingsDialog Reminders tab shows correct list
- [ ] TimerDialog shows correct entries
- [ ] No `reminderAt`/`reminderFired`/`reminderRepeat` fields written to tasks (after C5)

## Final Verification

- [ ] Fresh app launch — no task reminders in tasks.json
- [ ] Set a task reminder → appears in TimerManager + TimerDialog
- [ ] Timer fires → notification shows correct task text
- [ ] Clear reminder → removed from TimerManager
- [ ] Archive task → reminder cancelled
- [ ] Restore task → no reminder restored
- [ ] Delete task → reminder cancelled
- [ ] Repeating reminder → fires again at next interval
- [ ] Generic timer → still works as before
- [ ] SettingsDialog Reminders tab → shows task reminders
- [ ] Countdown label → updates every second
