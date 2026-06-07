# B4 — Fix Text Disappearing When Enabling Always-on-Top

## Problem
Toggling "Always on Top" (via shortcut Alt+T or Settings) causes task text to disappear until window is resized.

## Root Cause
`reconcile_layer_settings()` + `compose_main_window_flags()` recreates window flags, which triggers `setWindowFlags()` → `show()` → window recreation. This destroys/recreates the native window handle, losing layout state. The `render_tasks()` call in `apply_settings()` may run before layout settles.

## Files
- `C:\Users\Prosperr\Documents\_Remind\src\backend\window_layer.py`
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py`

---

## Fix 1: Preserve Geometry & State During Flag Change

In `main_window.py`, `toggle_always_on_top()` and `toggle_pinned_to_desktop()`:

```python
def toggle_always_on_top(self, checked: bool):
    self.app_state = self.state_manager.state
    self.app_state["alwaysOnTop"] = checked
    if checked:
        self.app_state["pinnedToDesktop"] = False
    reconcile_layer_settings(self.app_state)
    self.state_manager.save()
    
    # PRESERVE GEOMETRY BEFORE FLAG CHANGE
    geo = self.saveGeometry()
    self.apply_settings()
    self.restoreGeometry(geo)
```

Same for `toggle_pinned_to_desktop()` and `_toggle_pin_to_desktop_from_menu()`.

---

## Fix 2: Defer Render Until After Flag Change Settles

In `apply_settings()`, move `render_tasks()` to end with slight delay:

```python
def apply_settings(self):
    # ... existing code ...
    
    reconcile_layer_settings(self.app_state)
    self.setWindowFlags(
        compose_main_window_flags(
            self.app_state.get("pinnedToDesktop", False),
            self.app_state.get("alwaysOnTop", False),
        )
    )
    self.show()
    
    # ... pin/unpin ...
    
    self._restore_window_geometry()
    
    # DEFER RENDER TO NEXT EVENT LOOP
    QTimer.singleShot(0, self.render_tasks)
```

---

## Fix 3: Window Layer — Minimal Flag Changes

In `src/backend/window_layer.py`, `compose_main_window_flags()`:

```python
def compose_main_window_flags(pinned: bool, always_on_top: bool) -> Qt.WindowType:
    flags = Qt.WindowType.FramelessWindowHint
    if pinned:
        flags |= Qt.WindowType.WindowStaysOnBottomHint
    elif always_on_top:
        flags |= Qt.WindowType.WindowStaysOnTopHint
    # Tool flag prevents taskbar entry when pinned (optional)
    # if pinned: flags |= Qt.WindowType.Tool
    return flags
```

Ensure `reconcile_layer_settings()` only mutates the state dict, doesn't call `setWindowFlags()`.

---

## Code Quality
- **Geometry preservation:** `saveGeometry()`/`restoreGeometry()` handles position+size
- **Deferred render:** `QTimer.singleShot(0, ...)` lets window flags settle
- **Single flag composition:** All flag logic in one place
- **No redundant shows:** `apply_settings()` calls `show()` once

## Verification
- Enable Always-on-top via Alt+T → text remains visible
- Enable via Settings → Save → text remains visible
- Toggle Pin to Desktop → text remains visible
- Rapid toggle (on/off/on) → no text loss, no crashes
- Window position/size preserved after toggle