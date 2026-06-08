# Default window size fix — 380×380 on first launch

## Problem
Current default (520×700) takes up ~91% of a 1366×768 screen. On smaller screens the window is too large for a side-widget.

## Changes

### Step 1 — Update `src/backend/window_geometry.py`

```python
DEFAULT_WINDOW_WIDTH = 380
DEFAULT_WINDOW_HEIGHT = 380
MIN_WINDOW_WIDTH = 340
MIN_WINDOW_HEIGHT = 340
```

### Step 2 — Update `src/backend/state_manager.py` `default_window_geometry`

```python
@staticmethod
def default_window_geometry() -> dict:
    return {
        "windowPos": {"x": 100, "y": 100},
        "windowSize": {"w": 380, "h": 380},
    }
```

## Verification
1. Delete `appstate.json` (fresh state)
2. Launch Nudge → window opens at 380×380, positioned at (100, 100)
3. Resize down to minimum → stops at 340×340
4. Resize up → works correctly
5. Close and reopen → size persists