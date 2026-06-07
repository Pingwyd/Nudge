# B1 — System Tray Icon + Minimize to Tray

## Files
- **NEW:** `C:\Users\Prosperr\Documents\_Remind\src\os_layer\system_tray.py`
- **MODIFY:** `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py`

---

## 1. Create `src/os_layer/system_tray.py`

```python
"""System tray integration for Nudge."""
from __future__ import annotations
from typing import Callable, Optional
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal

class SystemTrayManager(QObject):
    """Manages system tray icon and context menu."""
    
    show_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, app: QApplication, icon: QIcon, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._app = app
        self._tray = QSystemTrayIcon(icon, app)
        self._tray.setToolTip("Nudge Task Widget")
        
        # Context menu
        menu = QMenu()
        show_action = QAction("Show", app)
        show_action.triggered.connect(self.show_requested.emit)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Quit", app)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)
        
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()
    
    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click = show
            self.show_requested.emit()
    
    def show_message(self, title: str, message: str, msecs: int = 3000):
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, msecs)
    
    def hide(self):
        self._tray.hide()
    
    def is_visible(self) -> bool:
        return self._tray.isVisible()
```

---

## 2. Integrate in `main_window.py`

### Imports (add at top)
```python
from src.os_layer.system_tray import SystemTrayManager
from src.backend.icon import get_app_icon  # already imported
```

### In `MainWindow.__init__()` (after `self.apply_settings()`)
```python
# System tray
self._tray = SystemTrayManager(QApplication.instance(), get_app_icon(), self)
self._tray.show_requested.connect(self._show_from_tray)
self._tray.quit_requested.connect(self._quit_from_tray)
```

### New Methods on MainWindow
```python
def _show_from_tray(self):
    """Restore window from tray."""
    self.showNormal()
    self.activateWindow()
    self.raise_()

def _quit_from_tray(self):
    """Full quit from tray menu."""
    self._tray.hide()
    QApplication.instance().quit()

def closeEvent(self, event):
    """Minimize to tray instead of closing, unless forced."""
    # Check if user explicitly chose "Quit" from tray (we set a flag)
    if getattr(self, '_force_quit', False):
        self._tray.hide()
        super().closeEvent(event)
        return
    
    # Default: hide to tray
    event.ignore()
    self.hide()
    self._tray.show_message("Nudge", "Still running in tray. Right-click tray icon to quit.")
```

### Modify Existing Close Behavior
- **Close button (✕)**: Minimizes to tray (current `self.close()` → triggers `closeEvent` → hides)
- **Escape shortcut**: Currently double-Esc quits. Keep that behavior — set `_force_quit = True` before `self.close()`
- **Tray "Quit"**: Calls `_quit_from_tray()` → sets flag → quits

### Update `_on_escape_pressed()`
```python
def _on_escape_pressed(self):
    if self.input_bar.hasFocus():
        self.input_bar.clear()
        return
    self._escape_count += 1
    if self._escape_count >= 2:
        self._escape_count = 0
        self._escape_timer.stop()
        self._force_quit = True
        self.close()
    else:
        self._escape_timer.start(500)  # 500ms window per spec
```

---

## Code Quality
- **Single responsibility:** Tray logic isolated in `system_tray.py`
- **Signal-based:** Clean decoupling from MainWindow
- **Resource cleanup:** `hide()` called on quit
- **Icon reuse:** Uses existing `get_app_icon()`

## Verification
- Run app → tray icon appears
- Click ✕ → window hides, tray shows "Still running..."
- Left-click tray → window restores
- Right-click tray → "Show" / "Quit" menu
- "Quit" → app fully exits
- Double-Esc → app fully exits
- Settings → "Check for updates" still works after tray hide/show