# Sprint 2 — Settings Restructure

## Sprint Header

- **Sprint #:** S2
- **Goal:** Restructure the Settings dialog: scope Reset to Defaults per-tab, move Reminders to its own tab, and fix theme styling for entry widgets.
- **Depends on:** S1 (Sprint 1 must be complete and verified)
- **Estimated chunks:** 5

---

## Features

### Feature 1: Reset to Defaults → Scoped to Active Tab

**User stories / requirements:**
- As a user, clicking "Reset to Defaults" should only reset the Settings tab I'm currently viewing, not all settings.
- Each tab has its own set of default values.
- Visual feedback when values snap back to defaults.

**Technical tasks:**
- Refactor `_reset_shortcuts_to_defaults` into a dispatcher that checks which tab is active via `self._stack.currentIndex()`.
- Create per-tab reset methods:
  - `_reset_general_defaults()` — startup, lock, pin, always-on-top, check-updates, boot-notification
  - `_reset_appearance_defaults()` — theme, text size, opacity
  - `_reset_shortcuts_defaults()` — existing logic (rename from `_reset_shortcuts_to_defaults`)
  - `_reset_export_defaults()` — format, include-history
  - `_reset_reminders_defaults()` — (future tab, stub for now)
- Store defaults as a class-level dict `DEFAULTS = {...}`.
- After resetting, mark dirty so user can save or discard.

**Files to modify:**
- `src/frontend/main_window.py` — SettingsDialog class

**Tests to write:**
- Manual: open General tab → change values → Reset → only General values reset.
- Manual: open Appearance tab → change theme → Reset → only Appearance resets.
- Manual: open Shortcuts tab → change shortcuts → Reset → only shortcuts reset.
- Manual: other tabs' values are untouched.

---

### Feature 2: Reminders → Own Settings Tab

**User stories / requirements:**
- As a user, Reminders management (pending task reminders list, Clear Selected) should be in its own dedicated tab in Settings, not buried in Advanced.
- The sidebar should show: General, Appearance, Shortcuts, Export, Reminders, Advanced, Help.

**Technical tasks:**
- Extract the "Pending Task Reminders" section from `advanced_tab` into a new `reminders_tab`.
- Add "Reminders" to the `tab_names` list and sidebar button creation.
- Move `_task_reminder_list`, `clear_reminder_btn`, and related methods (`_populate_task_reminder_list`, `_clear_selected_task_reminder`, `_edit_task_reminder_from_list`, `_clear_task_reminder_from_list`) to work with the new tab.
- Update `_open_reminders_from_settings` in Help tab to navigate to the Reminders tab (switch sidebar index) instead of opening a separate dialog.
- Add `_populate_task_reminder_list()` call after tab creation.

**Files to modify:**
- `src/frontend/main_window.py` — SettingsDialog.init_ui, tab names, sidebar

**Tests to write:**
- Manual: Settings → sidebar shows Reminders tab.
- Manual: Click Reminders → pending task reminders list appears.
- Manual: Advanced tab no longer shows reminder list.
- Manual: Help → Reminders button navigates to Reminders tab.

---

### Feature 3: Theme Fix for Entry Widgets

**User stories / requirements:**
- As a user, all entry widgets (QKeySequenceEdit, QListWidget, QComboBox, QSpinBox) should respect the active theme, including OLED.
- The keyboard shortcut rebinder cards (nestedPanel) should have theme-appropriate backgrounds and borders.
- The pending task reminders QListWidget should match the theme.

**Technical tasks:**
- Audit all QKeySequenceEdit widgets in the Shortcuts tab — they sit inside `nestedPanel` QFrame cards. Apply theme-aware background/border to the cards.
- Audit the `_task_reminder_list` QListWidget — apply theme-aware background/border/text.
- Audit QComboBox widgets (theme combo, export format combo) — apply theme-aware styling.
- Audit QSpinBox widgets (text size, opacity) — apply theme-aware styling.
- Create a helper method `_apply_entry_widget_theming()` in SettingsDialog that applies stylesheets to all entry widgets using tokens from `get_theme()`.
- Call this method after `init_ui()` and whenever the theme changes (on Save).

**Files to modify:**
- `src/frontend/main_window.py` — SettingsDialog (new helper method, call sites)
- Possibly `src/frontend/theme.py` — add token generators if needed for QKeySequenceEdit, QListWidget

**Tests to write:**
- Manual: switch to OLED → shortcut rebinder cards have OLED-appropriate backgrounds.
- Manual: switch to OLED → reminder list has OLED background.
- Manual: switch to Light → all entry widgets have light-appropriate styling.
- Manual: no invisible text or borders in any theme.

---

## Execution Prompts

### CHUNK FILE LIST:
- S2-F1-C1.md — Reset to Defaults: refactor to per-tab dispatcher
- S2-F2-C1.md — Reminders tab: extract from Advanced into own tab
- S2-F3-C1.md — Theme fix: audit and apply theme tokens to entry widgets
- S2-F3-C2.md — Theme fix: add theme.py token generators if needed

*(4 chunks — S2-F1 and S2-F2 are independent, S2-F3 depends on S2-F2 because the new Reminders tab needs theming.)*

---

*End of sprint-plan.md*
