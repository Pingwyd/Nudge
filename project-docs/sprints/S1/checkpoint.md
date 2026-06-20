# Sprint 1 — Checkpoint Questions

After Sprint 1 completes, verify the following before starting Sprint 2:

## 1. Smooth Window Drag
- [ ] Open Settings window → drag it fast across the screen → no visible stutter?
- [ ] Open History window → drag it fast → no stutter?
- [ ] Resize handles on MainWindow still work (FramelessChromeController unaffected)?
- [ ] Overlap opacity updates correctly when Settings/History overlaps MainWindow?

## 2. Undo Toast
- [ ] Complete a task → toast appears inside the app window boundary (not at screen edge)?
- [ ] Complete a task with a long name → toast wraps text, doesn't stretch to screen edge?
- [ ] Toast overlaps the task list content (floats on top)?
- [ ] Toast matches Dark theme styling?
- [ ] Toast matches Light theme styling?
- [ ] Toast matches OLED theme styling?
- [ ] Click Undo → task is restored?
- [ ] Wait 5 seconds → toast auto-dismisses?

## 3. Confirmation Dialogs
- [ ] Right-click task → Delete → confirmation dialog appears?
- [ ] Click Cancel → task is NOT deleted?
- [ ] Click Yes → task IS deleted?
- [ ] History → Clear All → confirmation dialog appears?
- [ ] Click Cancel → history is NOT cleared?
- [ ] Click Yes → history IS cleared?
- [ ] Settings → Reminders → Clear Selected → confirmation dialog appears?
- [ ] Click Cancel → reminders are NOT cleared?
- [ ] Click Yes → reminders ARE cleared?
- [ ] All confirmation dialogs match liquid-glass theme?

## 4. General
- [ ] App launches without errors?
- [ ] No regressions in existing functionality (task add/edit/delete, settings save, history restore)?
- [ ] Version bumped from 1.7.0 to 1.9.0?
