# S4 — Checkpoint

## Completion Status

| Chunk | Feature | Status |
|-------|---------|--------|
| S4-F1-C1 | History delete confirmation bypass + Clear All | ⬜ |
| S4-F2-C1 | History live search | ⬜ |
| S4-F3-C1 | Undo toast dismiss button | ⬜ |
| S4-F4-C1 | Group drag architecture | ⬜ |
| S4-F4-C2 | Group drag implementation | ⬜ |
| S4-F4-C3 | Group drag verification | ⬜ |
| S4-F5-C1 | Input bar horizontal scroll | ⬜ |

## Verification Checklist

- [ ] "Don't ask for confirmation" checkbox persists in appstate.json
- [ ] Checkbox suppresses individual delete confirmation
- [ ] Clear All button exists in History window
- [ ] Clear All respects checkbox setting
- [ ] Search bar filters history entries (case-insensitive)
- [ ] Empty search shows all entries
- [ ] X button on toast dismisses without undoing
- [ ] Group headers are draggable
- [ ] Internal group drops reorder groups correctly
- [ ] External group drops paste group name + tasks to text editor
- [ ] Drop indicator visible during group drag
- [ ] Input bar scrolls horizontally for long text
- [ ] Edit task field scrolls horizontally
- [ ] No regressions in existing task drag behavior

## Files Modified

- `src/frontend/main_window.py` — HistoryDialog, UndoToast, MainWindow
- `src/frontend/task_group_section.py` — group drag events
- `src/frontend/theme.py` — checkbox/search bar styling
