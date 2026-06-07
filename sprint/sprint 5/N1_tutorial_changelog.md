# N1 — Tutorial Refresh + "What's New" Changelog Popup

## Files
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py` — `TutorialDialog`, `MainWindow`
- `C:\Users\Prosperr\Documents\_Remind\src\backend\updater.py` — parse changelog

---

## Part A: Refresh Tutorial Dialog

Update the existing `TutorialDialog` (around line 586-677 in main_window.py) with additional/updated features:

**Current features list (update as needed):**
- Add a task, Auto-scroll, Mark done, Edit/Delete, Groups, Drag to reorder
- Drag text out, History, Settings (5 tabs), Always on Top, Export, Resize, Quick Quit

**Add new features to the tutorial:**
- "Check for updates" — Settings check + ↻ button
- "Tray icon" — Right-click tray to show/quit
- "Buy Me a Coffee" — Support development

**Also update the app name references** — the tutorial says "Nudge" (correct).

---

## Part B: "What's New" Post-Update Popup

After an auto-update completes and the app relaunches, show a "What's New" dialog that displays the changelog from the release in user-friendly language.

### Detection Mechanism
Store the previous version in `appstate.json`:
```python
# StateManager defaults — add:
"lastSeenVersion": "1.1.0"
```

On boot, in `MainWindow.__init__()`:
```python
# After apply_settings():
last_seen = self.app_state.get("lastSeenVersion", "1.1.0")
current = __version__
if current > last_seen:
    # Show "What's New" dialog
    QTimer.singleShot(1000, self._show_whats_new)
    self.app_state["lastSeenVersion"] = current
    self.state_manager.save()
```

### Create Simple "What's New" Dialog
Reuse or adapt `UpdateInfoDialog` but with different title/buttons:

```python
def _show_whats_new(self):
    """Show changelog after update."""
    # Fetch or use stored changelog
    changelog = self.app_state.get("lastChangelog", "Bug fixes and improvements.")
    
    dialog = UpdateInfoDialog(
        latest_version=__version__,
        changelog=changelog,
        download_url="",
        parent=self,
    )
    dialog.setWindowTitle("What's New in Nudge")
    # Rename button
    # (Or create a simpler WhatsNewDialog)
    
    avoid = self._window_rects_to_avoid()
    self._place_dialog_avoiding_rects(dialog, avoid)
    # Only "Got it!" button — no download
    # Accept/reject both just close
    dialog.exec()
```

Alternatively, create `src/frontend/whats_new_dialog.py` following the same Liquid Glass pattern but simpler:

- Title: "What's New in Nudge v{version}"
- QTextEdit with changelog (read-only)
- Single "Got it!" button → accept

## Code Quality
- **Non-blocking:** Dialogs shown after app is ready (QTimer delay)
- **Single-show:** `lastSeenVersion` prevents showing again until next update
- **Persistent changelog:** Store last changelog in `appstate.json` so it can show even without network

## Verification
- After update from 1.1.0 to 1.1.1 → "What's New" popup shows on first launch
- Changelog displays release notes
- "Got it!" → dismisses, no more popup on subsequent launches
- Clean install (no previous version) → no popup