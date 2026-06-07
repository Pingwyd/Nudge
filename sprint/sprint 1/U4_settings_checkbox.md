# U4 — Settings Checkbox "Check for updates at startup"

## File
`C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py` — `SettingsDialog` class

## Changes

### 1. Add checkbox in General tab (after `always_on_top_cb`)
In `SettingsDialog.init_ui()`, locate the General tab section (around line 802-823). After the `always_on_top_cb` and its signal connections, add:

```python
# Check for updates
self.check_updates_cb = self._create_checkbox_row(
    "Check for updates at startup",
    self.state_manager.state.get("checkForUpdates", True),
)
general_layout.addWidget(self.check_updates_cb)
```

### 2. Update `_build_snapshot()` to include the new setting
Locate `_build_snapshot()` (around line 693-708). Add to the returned dict:

```python
"checkForUpdates": self.check_updates_cb.isChecked(),
```

### 3. Update `save_changes()` to persist the setting
Locate `save_changes()` (around line 1291-1343). After saving `groupsEnabled`, add:

```python
self.state_manager.state["checkForUpdates"] = self.check_updates_cb.isChecked()
```

## Code Quality Requirements
- Use existing `_create_checkbox_row()` helper (consistent styling, auto-connects `_mark_dirty`)
- Keep alphabetical/semantic grouping in snapshot (add near other boolean flags)
- No hardcoded defaults — read from `state_manager.state.get("checkForUpdates", True)`
- The checkbox should immediately mark dirty when toggled (handled by `_create_checkbox_row`)

## Verification
- Open Settings → General tab → "Check for updates at startup" checkbox visible
- Toggle → Save → Close → Reopen Settings → state persists
- `appstate.json` contains `"checkForUpdates": true/false`

## Location Reference
- General tab starts ~line 802
- `_build_snapshot` ~line 693
- `save_changes` ~line 1291