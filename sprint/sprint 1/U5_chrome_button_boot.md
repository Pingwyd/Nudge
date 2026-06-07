# U5 — Chrome Button + Boot Check + Update Methods

## File
`C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py` — `MainWindow` class

## Required Imports (add at top of file)
```python
from src import __version__
from src.backend.updater import check_for_update, perform_update
from src.frontend.update_dialog import UpdateInfoDialog
import threading
```

---

## 1. Chrome Update Button (in `MainWindow.init_ui()`)

Locate the top bar chrome button section (around line 1645-1690). The current order is:
`btn_feedback` → `btn_history` → `btn_settings` → `btn_minimize` → `btn_exit`

**Add update button between `btn_settings` and `btn_minimize`:**

```python
# Update check button (placed after Settings, before Minimize)
self.btn_update = QPushButton("\u21bb")  # ↻ refresh symbol
self.btn_update.setObjectName("chromeButton")
self.btn_update.setFixedSize(chrome_btn_sz, chrome_btn_sz)
self.btn_update.setToolTip("Check for updates")
self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
self.btn_update.clicked.connect(self._manual_update_check)
top_bar.addWidget(self.btn_update)
```

**Also update `apply_app_theme()` to refresh the update button icon color:**
In `apply_app_theme()` (around line 1088-1099), the `chrome_color` is already computed. No change needed since the button uses `chromeButton` style which picks up the theme color automatically.

---

## 2. Boot-Time Check (in `MainWindow.__init__()`)

Locate the end of `__init__` (around line 1436-1441), after `self.apply_settings()`:

```python
# Boot-time update check (if enabled)
if self.app_state.get("checkForUpdates", True):
    QTimer.singleShot(3000, self._check_and_prompt_update)
```

---

## 3. New Methods on MainWindow

Add these methods after `apply_settings()` (around line 1130):

### `_check_and_prompt_update()`
```python
def _check_and_prompt_update(self):
    """Check for updates in background thread; show dialog if available."""
    def _worker():
        # Read URL from state (allows future config change)
        check_url = self.app_state.get("updateCheckUrl", "https://api.github.com/repos/user/nudge/releases/latest")
        result = check_for_update(__version__, check_url)
        if result and result.available:
            # Must run UI on main thread
            QTimer.singleShot(0, lambda: self._show_update_dialog(result))
    
    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
```

### `_manual_update_check()`
```python
def _manual_update_check(self):
    """Triggered by chrome ↻ button — shows 'Checking...' feedback."""
    # Optional: show brief "Checking..." toast or status
    self._check_and_prompt_update()
```

### `_show_update_dialog(result)`
```python
def _show_update_dialog(self, result):
    """Display the UpdateInfoDialog positioned to avoid overlap."""
    dialog = UpdateInfoDialog(
        result.latest_version,
        result.changelog,
        result.download_url,
        self,
    )
    avoid = self._window_rects_to_avoid()
    self._place_dialog_avoiding_rects(dialog, avoid)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        self._apply_update(result.download_url, result.latest_version)
```

### `_apply_update(download_url, version)`
```python
def _apply_update(self, download_url: str, version: str):
    """Download and install update; close app on success."""
    # Modal "Downloading..." message (no buttons, stays on top)
    msg = QMessageBox(self)
    msg.setWindowTitle("Updating Nudge")
    msg.setText(f"Downloading v{version}...")
    msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
    msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    msg.show()
    QApplication.processEvents()

    ok = perform_update(download_url, version)
    msg.close()

    if ok:
        # App will be restarted by installer script
        self.close()
    else:
        QMessageBox.warning(
            self, "Update Failed",
            "Could not download the update. Please check your connection and try again."
        )
```

---

## Code Quality Requirements
- **Thread safety:** Network call in background thread; UI updates via `QTimer.singleShot(0, ...)`
- **Error handling:** Network failures silent on boot; manual check shows warning
- **Theme consistency:** Update button uses existing `chromeButton` style
- **Positioning:** Reuse `_place_dialog_avoiding_rects()` so dialog doesn't overlap Settings/History
- **Clean shutdown:** `self.close()` triggers normal `closeEvent` → geometry save

## Verification
- Launch app → 3s later, if update available → dialog appears
- Click ↻ button → manual check runs
- "Download & Install" → "Downloading..." shows → app closes → PS script runs → app relaunches as new version
- Settings checkbox off → no boot check

## Location Reference
- `MainWindow.init_ui` chrome buttons: ~line 1645
- `MainWindow.__init__` end: ~line 1436
- `apply_settings`: ~line 1101
- Add new methods after `apply_settings`