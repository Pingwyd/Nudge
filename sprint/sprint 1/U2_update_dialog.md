# U2 — Create src/frontend/update_dialog.py

## Context
- **Style:** Match existing Liquid Glass dialogs (`HistoryDialog`, `SettingsDialog`, `TutorialDialog`)
- **Parent:** `MainWindow` passes `self` as parent
- **Theme:** Use `src/frontend/theme.py` tokens via `get_theme()`, `normalize_theme_id()`, `refresh_glass_shells()`

## Requirements

Create `C:\Users\Prosperr\Documents\_Remind\src\frontend\update_dialog.py`

### Class: `UpdateInfoDialog(QDialog)`

**Constructor:**
```python
def __init__(self, latest_version: str, changelog: str, download_url: str, parent=None):
```

**Window setup:**
- `FramelessWindowHint | Dialog`
- `WA_TranslucentBackground`
- Resize: 420×480, min 320×360
- Title: "Update Available"

**Layout (QVBoxLayout on QFrame#glassPanel):**

| Element | Details |
|---------|---------|
| **Title** | `f"Update Available — Nudge v{latest_version}"` — bold 16px, centered |
| **Current version** | `f"Current version: {__version__}"` — 12px, centered, muted (currently `1.1.0`) |
| **Changelog label** | "What's new:" — bold 14px |
| **Changelog content** | `QScrollArea` → `QTextEdit(readOnly=True)` — plain text, scrollable, takes remaining space |
| **Note** | "The app will restart after installing." — 10px, centered, muted |
| **Buttons** | Horizontal row: "Remind Me Later" (reject) + "Download & Install" (accept, bold) |

**Behavior:**
- Draggable: `mousePressEvent`/`mouseMoveEvent` store `_drag_pos`
- Overlap opacity: `moveEvent` → `_update_overlap_opacity()` (same pattern as `HistoryDialog`):
  - If overlapping parent: solid background + border
  - Else: `refresh_glass_shells(self, theme_id)`
- `resizeEvent`: update frame geometry

**Imports needed:**
```python
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTextEdit, QVBoxLayout, QWidget)
from src import __version__
from src.frontend.theme import get_theme, normalize_theme_id, refresh_glass_shells
```

## Verification
- Import works: `from src.frontend.update_dialog import UpdateInfoDialog`
- Instantiate with test data → dialog renders with Liquid Glass styling
- Draggable by title area
- Buttons return `Accepted`/`Rejected` correctly
- Overlap detection works when moved over parent window

## Reference Pattern
See `src/frontend/history_dialog.py` for the exact Frameless + translucent + glassPanel + draggable + overlap pattern to copy.