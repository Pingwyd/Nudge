# Sprint 2 — Checkpoint Questions

After Sprint 2 completes, verify the following before starting Sprint 3:

## 1. Reset to Defaults (Scoped)
- [ ] Open General tab → change startup, lock, pin → Reset → only General values reset?
- [ ] Open Appearance tab → change theme to Light → Reset → theme reverts to Dark, text size and opacity unchanged?
- [ ] Open Shortcuts tab → change History shortcut → Reset → only shortcuts reset?
- [ ] Open Export tab → change format to CSV → Reset → format reverts to TXT?
- [ ] After reset on any tab, other tabs' values are untouched?
- [ ] After reset, Save button becomes active (dirty state)?

## 2. Reminders Tab
- [ ] Settings sidebar shows: General, Appearance, Shortcuts, Export, Reminders, Advanced, Help?
- [ ] Clicking "Reminders" shows pending task reminders list?
- [ ] Advanced tab no longer shows reminder list?
- [ ] Help → Reminders button navigates to Reminders tab (not a separate dialog)?
- [ ] Clear Selected button works in Reminders tab (with confirmation)?
- [ ] Pending task reminders list populates correctly?

## 3. Theme Fix
- [ ] OLED theme → QKeySequenceEdit widgets have OLED background/border?
- [ ] OLED theme → QListWidget has OLED background?
- [ ] OLED theme → QComboBox widgets have OLED styling?
- [ ] Light theme → all entry widgets have light-appropriate styling?
- [ ] Dark theme → all entry widgets have dark-appropriate styling?
- [ ] No invisible text or invisible borders in any theme?
- [ ] New generators in theme.py (if added) are importable?

## 4. General
- [ ] App launches without errors?
- [ ] No regressions in existing functionality?
- [ ] All Sprint 1 fixes still work (smooth drag, undo toast, confirmation dialogs)?
