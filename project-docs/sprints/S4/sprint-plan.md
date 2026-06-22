# Sprint 4 — History UX, Group Drag, Input Scroll

**Sprint:** S4
**Phase:** 4 (History UX, Group Drag, Input Scroll)
**Duration:** 1.5 days
**Version:** v1.10

---

## Features

### S4-F1: History Delete Confirmation Bypass + Clear All
**Problem:** Repetitive confirmation dialogs slow down history cleanup. No Clear All button exists.
**Approach:** Add checkbox to skip delete confirmations + Clear All button at bottom of History.

### S4-F2: History Live Search
**Problem:** Users with many completed tasks can't quickly find a specific entry.
**Approach:** Add QLineEdit search bar with live filtering via textChanged signal.

### S4-F3: Undo Toast Dismiss Button
**Problem:** Users must wait for 5-second timeout to dismiss undo toast.
**Approach:** Add X button to right side of UndoToast that dismisses without undoing.

### S4-F4: Group Drag-and-Reorder + Drag Out to Text Editor
**Problem:** Groups can only be reordered manually. No way to drag a group's tasks to a text editor.
**Approach:** Make group headers draggable with QDrag. Internal drops reorder groups; external drops paste group name + tasks as plain text.

### S4-F5: Input Bar Horizontal Scrolling
**Problem:** Long task text in input bar gets clipped or cursor jumps to end.
**Approach:** Verify/fix QLineEdit horizontal scroll behavior in add-task and edit-task fields.

---

## Chunks

| Chunk | Feature | Model | Type | Touches Existing | Depends on |
|-------|---------|-------|------|------------------|-----------|
| S4-F1-C1 | Add checkbox + Clear All to HistoryDialog | DeepSeek V4 Flash | Pure-Logic | Yes | none |
| S4-F2-C1 | Add search bar + live filter to HistoryDialog | DeepSeek V4 Flash | Pure-Logic | Yes | S4-F1-C1 |
| S4-F3-C1 | Add X button to UndoToast | DeepSeek V4 Flash | Pure-Logic | Yes | none |
| S4-F4-C1 | Group drag + drop reorder + external paste | MiMo V2.5 | Architecture-Reasoning | Yes | none |
| S4-F4-C2 | Implement group drag with QDrag + MIME types | DeepSeek V4 Flash | Pure-Logic | Yes | S4-F4-C1 |
| S4-F4-C3 | Verify group drag in all scenarios | MiMo V2.5 | Integration-Test | Yes | S4-F4-C2 |
| S4-F5-C1 | Fix input bar horizontal scroll | DeepSeek V4 Flash | Pure-Logic | Yes | none |

---

## Sequencing Map

```
S4-F1-C1 ──→ S4-F2-C1
S4-F3-C1 (parallel)
S4-F4-C1 ──→ S4-F4-C2 ──→ S4-F4-C3
S4-F5-C1 (parallel)
```

**Parallelizable waves:**
- Wave 1: S4-F1-C1, S4-F3-C1, S4-F4-C1, S4-F5-C1
- Wave 2: S4-F2-C1, S4-F4-C2
- Wave 3: S4-F4-C3

---

## Checkpoint Questions

After S4:
- [ ] Does the "Don't ask for confirmation" checkbox persist across sessions?
- [ ] Does Clear All respect the checkbox setting?
- [ ] Does the search bar filter history entries as you type?
- [ ] Does the X button on the undo toast dismiss without undoing?
- [ ] Can you drag group headers to reorder groups?
- [ ] Can you drag a group outside the app and drop into Notepad?
- [ ] Does the input bar scroll horizontally for long text?
