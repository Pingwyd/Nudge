# R2–R7 — Combined Backlog Verification Bundle

## Important
These are **verify-only** tasks. Read the specified code, confirm it's working, and print "Verified" for each. Only make changes if something is clearly broken.

---

## R2 — History/Settings Shortcut Toggle (M3)

**Read:** `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py`

**Check:**
- `open_history()` (around line 1937): `if self._history_dialog is not None: self._history_dialog.close(); return`
- `open_settings()` (around line 1951): `if self._settings_dialog is not None: self._settings_dialog.close(); return`
- `SettingsDialog.closeEvent()` (around line 1359): Shows unsaved changes prompt via `ThemedMessageDialog.question`
- Shortcuts in `update_keyboard_shortcuts()` use `Qt.ShortcutContext.ApplicationShortcut`

**Result:** Already implemented. Print "R2 verified."

---

## R3 — Context Menu Theme (M7)

**Read:** `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py`

**Check:**
- `_style_context_menu(menu)` (around line 1636): calls `menu.setStyleSheet(menu_stylesheet(theme))`
- `show_task_context_menu()` calls `_style_context_menu(menu)` on line 1643
- `contextMenuEvent()` calls `_style_context_menu(menu)` on line 1757
- `_show_group_header_menu()` calls `_style_context_menu(menu)` on line 1522

**Result:** Already implemented. Print "R3 verified."

---

## R4 — Group "+" Button Visible (M8)

**Read:** `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py` around line 1289-1294 and `C:\Users\Prosperr\Documents\_Remind\src\frontend\theme.py` line 462-478.

**Check:**
- `btn_add_group` uses objectName `accentIconButton`
- `accent_icon_button_stylesheet()` in theme.py provides visible styling:
  - `background: {accent_button_bg}`
  - `border: 1px solid {border}`
  - `font-size: 20px; font-weight: bold;`
  - `min-height: 22px`
- Button is 32x28px with `+` text

**Result:** Already implemented. If the + is still hard to see, add:
```python
self.btn_add_group.setStyleSheet(self.btn_add_group.styleSheet() + "font-size: 22px; font-weight: bold;")
```
Print "R4 verified (or fix applied)."

---

## R5 — Light Theme Toolbar Icons Darker (M9)

**Read:** `C:\Users\Prosperr\Documents\_Remind\src\frontend\theme.py`

**Check:**
- `LIGHT_THEME["colors"]["chrome_icon"]` = `"#2c2c2e"` (dark color for light mode)
- `_chrome_button_color(theme)` returns `theme["colors"].get("chrome_icon", _c(theme, "text"))`
- `chrome_button_stylesheet(theme)` uses `chrome_color` for text color
- `MainWindow.apply_app_theme()` passes `chrome_color` to `_history_toolbar_icon()`

**Result:** Already implemented. Print "R5 verified."

---

## R6 — Liquid Glass Scrollbars (M10)

**Read:** `C:\Users\Prosperr\Documents\_Remind\src\frontend\theme.py` lines 301-347.

**Check:**
- `scroll_bar_stylesheet(theme)` exists and uses theme tokens:
  - `scrollbar_track` for background
  - `scrollbar` for handle
  - `hover` for handle:hover
  - `hover_strong` for handle:pressed
- Scrollbar is 10px wide with rounded corners
- Included in `build_application_stylesheet()`

**Result:** Already implemented. Print "R6 verified."

---

## R7 — Export "Open Folder?" Prompt

**Read:** `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py` around line 1282-1289.

**Check:**
```python
if ThemedMessageDialog.question(
    self, "Export Complete",
    f"Tasks exported successfully to:\n{path}\n\nDo you want to open the file location?",
    yes_label="Open file location",
    no_label="Close",
):
    import os
    os.startfile(str(path.parent))
```

**Result:** Already implemented. Print "R7 verified."

---

## Summary
After running all checks, print the verification results table:

| Task | Status |
|------|--------|
| R2 (M3) | Verified |
| R3 (M7) | Verified |
| R4 (M8) | Verified |
| R5 (M9) | Verified |
| R6 (M10) | Verified |
| R7 (Export) | Verified |