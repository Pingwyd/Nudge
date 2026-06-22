# Sprint 2 — Medium Severity Fixes

**Sprint:** S2
**Phase:** 2 (Medium Severity)
**Duration:** 1 day
**Bugs:** B3a (toast position), B3b (task restore position), B4 (shortcut toggle)

---

## Features

### S2-F1: Undo Toast Positioning
**Bug:** B3a — Toast can clip outside window view
**Root cause:** `_reposition()` uses fixed coordinates with no bounds checking

### S2-F2: Task Restore Position
**Bug:** B3b — Restored task reappears at bottom of list
**Root cause:** `restore_task_from_history` appends; no index saved at archive time

### S2-F3: Dialog Shortcut Toggle
**Bug:** B4 — Ctrl+H doesn't close History dialog
**Root cause:** `HistoryDialog` doesn't emit `finished` on close

---

## Chunks

| Chunk | Feature | Model | Type | Depends on |
|-------|---------|-------|------|-----------|
| S2-F1-C1 | Implement smart toast positioning | DeepSeek V4 Flash | Pure-Logic | none |
| S2-F1-C2 | Verify toast positioning edge cases | MiMo V2.5 | Integration-Test | S2-F1-C1 |
| S2-F2-C1 | Save archive index + restore to position | MiMo V2.5 | Architecture-Reasoning | none |
| S2-F2-C2 | Implement position-preserving restore | DeepSeek V4 Flash | Pure-Logic | S2-F2-C1 |
| S2-F2-C3 | Verify restore with groups | MiMo V2.5 | Integration-Test | S2-F2-C2 |
| S2-F3-C1 | Fix GlassPanelDialog closeEvent | DeepSeek V4 Flash | Pure-Logic | none |
| S2-F3-C2 | Verify toggle for all dialogs | MiMo V2.5 | Integration-Test | S2-F3-C1 |

---

## Sequencing Map

```
S2-F1-C1 ──► S2-F1-C2
S2-F2-C1 ──► S2-F2-C2 ──► S2-F2-C3
S2-F3-C1 ──► S2-F3-C2

All three features are INDEPENDENT — can run in parallel.
```

---

## Checkpoint Questions

After S2-F1-C2:
- [ ] Does toast appear at bottom-left when it fits?
- [ ] Does toast appear at bottom-right outside window when it doesn't fit?
- [ ] Does toast position update on window resize?

After S2-F2-C3:
- [ ] Does undoing a task restore it to its original position (flat mode)?
- [ ] Does undoing a task restore it to its original position (grouped mode)?
- [ ] What happens if the task list changed while the task was archived?

After S2-F3-C2:
- [ ] Does Ctrl+H close an open History dialog?
- [ ] Does Ctrl+H reopen History after closing?
- [ ] Does Ctrl+, close an open Settings dialog? (Already works — verify no regression)
