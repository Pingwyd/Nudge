# B8 — Confirmation Dialog on Close

## Problem
Clicking the ✕ close button immediately hides the app to tray. There's no confirmation when actually quitting (via tray "Quit" or double-Esc). Users may accidentally close without knowing the app is still running in tray.

## Files
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py` — `closeEvent()`, tray integration

## Dependencies
- **Requires B1 (Tray Icon)** — this feature builds on the tray minimize behavior

---

## Changes

### 1. Update `closeEvent()` in MainWindow

The current `closeEvent()` (from B1) minimizes to tray silently. Add a confirmation when trying to **fully quit**:

```python
def closeEvent(self, event):
    """Handle close: minimize to tray with notification, or confirm full quit."""
    if getattr(self, '_force_quit', False):
        # Double-Esc or tray "Quit" → confirm before quitting
        reply = QMessageBox.question(
            self,
            "Quit Nudge?",
            "Are you sure you want to quit Nudge?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._tray.hide()
            event.accept()
            QApplication.instance().quit()
        else:
            event.ignore()
            self._force_quit = False
        return
    
    # Normal close → minimize to tray
    event.ignore()
    self.hide()
    
    # Only show notification if not already shown recently
    if not getattr(self, '_tray_notified', False):
        self._tray.show_message(
            "Nudge is still running",
            "Right-click the tray icon to show or quit."
        )
        self._tray_notified = True
        # Reset flag after 10 seconds so it can show again
        QTimer.singleShot(10000, lambda: setattr(self, '_tray_notified', False))
```

### 2. Update Tray "Quit" Handler

```python
def _quit_from_tray(self):
    """Full quit from tray menu — shows confirmation."""
    self._force_quit = True
    self.close()  # Triggers closeEvent which shows confirmation
```

### 3. Update Double-Esc Handler

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
        self.close()  # Triggers closeEvent with confirmation
    else:
        self._escape_timer.start(500)
```

### 4. Update Settings Dialog Close Event

The Settings dialog already has its own `closeEvent` for unsaved changes. No change needed there.

---

## UX Flow

| Action | Result |
|--------|--------|
| Click ✕ on main window | Minimizes to tray, shows tray notification (once per 10s) |
| Left-click tray icon | Restores window |
| Right-click tray → "Show" | Restores window |
| Right-click tray → "Quit" | Confirmation dialog → Yes = quit, No = cancel |
| Double-Esc | Confirmation dialog → Yes = quit, No = cancel |
| App restart via update | No confirmation (update sets `_skip_close_confirm = True`) |

---

## Update Method `_apply_update()` — Skip Confirmation During Auto-Update

```python
def _apply_update(self, download_url: str, version: str):
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
        # Skip confirmation — update is intentional
        self._force_quit = True
        self._skip_close_confirm = True  # Add this flag
        self.close()
    else:
        QMessageBox.warning(self, "Update Failed", "Could not download the update.")
```

In `closeEvent`, check `_skip_close_confirm`:
```python
if getattr(self, '_force_quit', False):
    if getattr(self, '_skip_close_confirm', False):
        self._tray.hide()
        event.accept()
        QApplication.instance().quit()
        return
    # ... normal confirmation dialog ...
```

---

## Code Quality
- **Consistent UX:** Close button = minimize to tray (not quit). Quit always requires explicit action (tray menu or double-Esc)
- **Non-intrusive notification:** Tray notification shown at most once per 10 seconds
- **Update bypass:** Auto-update skips confirmation — intentional action already taken
- **Default No:** Confirmation defaults to "No" — prevents accidental quit

## Verification
- Click ✕ → window hides, tray shows notification
- Click tray icon → window restores
- Right-click tray → "Quit" → confirmation dialog appears
- Click "No" → nothing happens, app still running
- Click "Yes" → app fully quits
- Double-Esc → confirmation dialog appears
- Auto-update → downloads, installs, shuts down without confirmation
- Notification not spammed — only shows once per 10s