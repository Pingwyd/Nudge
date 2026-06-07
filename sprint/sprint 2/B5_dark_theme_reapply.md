# B5 — Fix Dark Theme Not Fully Applying When Switching Back

## Problem
When switching from Light theme back to Dark, some parts of the Settings dialog and other panels remain in light-styled colors. Full app restart sometimes needed.

## Root Cause
`refresh_glass_shells()` only targets `QFrame#glassPanel` children via `findChildren(QFrame)`, but:

1. `QStackedWidget` pages inside Settings dialog are not repolished
2. Nested panels (`nestedPanel`, `transparentSurface`) miss repolish
3. `chromeButton` stylesheet not reapplied to existing button instances
4. `unpolish()`/`polish()` cycle doesn't reach deeply nested widgets

## Files
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\theme.py`
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py`

---

## Fix 1: Improve `refresh_glass_shells()` in `theme.py`

Replace the current implementation with a more thorough recursive repolish:

```python
def refresh_glass_shells(
    root: QWidget,
    theme: dict | str | None = None,
) -> None:
    """Full repolish of all styled widgets to guarantee theme consistency."""
    if isinstance(theme, str):
        resolved = get_theme(theme)
    else:
        resolved = deepcopy(theme or DARK_THEME)

    # 1. Re-apply glass panel stylesheets
    panel_css = glass_panel_stylesheet(resolved)
    for frame in root.findChildren(QFrame):
        if frame.objectName() == "glassPanel":
            frame.setStyleSheet(panel_css)
    
    # 2. Reapply nested panel style
    nested_css = nested_panel_stylesheet(resolved)
    for frame in root.findChildren(QFrame):
        if frame.objectName() == "nestedPanel":
            frame.setStyleSheet(nested_css)
    
    # 3. Force full style repolish on ALL widgets in the hierarchy
    style = root.style()
    if style is None:
        root.update()
        return
    
    all_widgets = [root] + root.findChildren(QWidget, options=Qt.FindChildOption.FindChildrenRecursively)
    for widget in all_widgets:
        style.unpolish(widget)
        style.polish(widget)
        widget.update()
    
    root.update()
```

Also add `nested_panel_stylesheet()` to `theme.py`:

```python
def nested_panel_stylesheet(theme: dict) -> str:
    return f"""
        QWidget#nestedPanel {{
            background: {_c(theme, "input_bg")};
            border: 1px solid {_c(theme, "menu_border")};
            border-radius: {_r(theme, "small")}px;
            padding: 0px;
        }}
    """
```

And add it to `build_application_stylesheet()`:

```python
def build_application_stylesheet(theme: dict | None = None) -> str:
    theme = theme or DARK_THEME
    sections = [
        # ... existing ...
        nested_panel_stylesheet(theme),  # ADD THIS
        # ... rest ...
    ]
    return "\n".join(sections)
```

---

## Fix 2: Call `refresh_glass_shells` on Parent After Theme Save

In `SettingsDialog.save_changes()`, after the existing `refresh_glass_shells(self, ...)` call, also call on the parent (main window):

```python
# After existing refresh_glass_shells(self, ...)
if parent is not None:
    refresh_glass_shells(parent, normalize_theme_id(self.state_manager.state.get("theme", "dark")))
```

---

## Fix 3: Reapply Chrome Button Styles in `apply_app_theme()`

In `MainWindow.apply_app_theme()`:

```python
def apply_app_theme(self) -> None:
    app = QApplication.instance()
    if app is None:
        return
    theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
    apply_theme_to_app(app, theme_id)
    theme = get_theme(theme_id)
    chrome_color = theme["colors"].get("chrome_icon", theme["colors"]["text"])
    self.btn_history.setIcon(_history_toolbar_icon(16, chrome_color))
    
    # Re-style the settings gear icon to use new chrome_color
    self.btn_settings.setStyleSheet("")  # Clear inline, let global QSS take over
```

---

## Code Quality
- **Recursive repolish:** `FindChildrenRecursively` ensures all nesting levels
- **Complete coverage:** glassPanel, nestedPanel, transparentSurface, chrome buttons all repolished
- **No inline QSS leaks:** Clearing inline styles lets global QSS win
- **Consistent entry point:** Both `save_changes()` paths (Settings save + app boot) call the same `refresh_glass_shells` pattern

## Verification
- Settings → Light → Save → Settings dialog shows light theme
- Settings → Dark → Save → Every part of Settings dialog is dark (tabs, content, buttons, scrollbars)
- Close Settings → Main window is fully dark
- Switch again → no light leftovers anywhere
- Check `nestedPanel` cards, `transparentSurface` areas, chrome buttons