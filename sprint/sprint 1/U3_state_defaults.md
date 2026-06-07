# U3 — Add checkForUpdates defaults to StateManager

## File
`C:\Users\Prosperr\Documents\_Remind\src\backend\state_manager.py`

## Change
In `StateManager.__init__()`, locate the `self.state` dict (around line 29-44). Add two new keys at the end:

```python
self.state = {
    "windowPos": {"x": 100, "y": 100},
    "windowSize": {"w": DEFAULT_WINDOW_WIDTH, "h": DEFAULT_WINDOW_HEIGHT},
    "pinned": False,
    "startOnBoot": False,
    "opacity": 1.0,
    "positionLocked": False,
    "alwaysOnTop": False,
    "theme": "dark",
    "taskTextSize": 14,
    "historyShortcut": "Ctrl+H",
    "settingsShortcut": "Ctrl+,",
    "pinShortcut": "Ctrl+P",
    "groupsEnabled": False,
    "lastExportDir": "",
    # NEW — add these two:
    "checkForUpdates": True,
    "updateCheckUrl": "https://api.github.com/repos/user/nudge/releases/latest"
}
```

## Verification
- Run app fresh (delete `appstate.json`) → `state_manager.state["checkForUpdates"] == True`
- `state_manager.state["updateCheckUrl"]` returns the GitHub API URL
- Existing settings load still works (missing keys get defaults)

## Notes
- `checkForUpdates: True` = enabled by default
- `updateCheckUrl` allows changing the endpoint without code change (future-proof)