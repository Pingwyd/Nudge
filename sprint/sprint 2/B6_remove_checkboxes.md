# B6 — Remove Checkboxes Beside Tasks

## Problem
The checkbox beside each task is redundant — clicking anywhere on the task already sends it to history. The checkbox adds visual clutter and doesn't serve a purpose.

## Files
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py` — `TaskRowWidget`, `render_tasks()`, `toggle_task()`
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\responsive_text.py` — `available_text_width()` (reserved widgets change)

---

## Changes

### 1. Remove Checkbox from `TaskRowWidget`

In `TaskRowWidget.__init__`:
- Remove `self.checkbox` creation
- Remove `self.checkbox` from layout
- Remove `self.checkbox` signal connections
- Remove `self.checkbox` from `reserved` list
- Update `mouseReleaseEvent` to toggle task directly instead of toggling checkbox

**New layout:** `[content_indent] [content_stack] [edit_btn]` — no checkbox

### 2. Update `mouseReleaseEvent` in `TaskRowWidget`

```python
def mouseReleaseEvent(self, event):
    if self._editing:
        return super().mouseReleaseEvent(event)
    if event.button() == Qt.MouseButton.LeftButton:
        pos = event.position().toPoint()
        clicked_child = self.childAt(pos)
        if clicked_child not in (self.edit_btn, self.editor):
            # Click toggles task done state
            if self.on_toggled:
                self.on_toggled(True)
            event.accept()
            return
    super().mouseReleaseEvent(event)
```

### 3. Update `_sync_content_stack_height()` — Remove Checkbox from Reserved

```python
def _sync_content_stack_height(self):
    ht_reserved = [self.edit_btn]
    if self._indent_spacer is not None:
        ht_reserved.insert(0, self._indent_spacer)
    column_width = available_text_width(self, ht_reserved)
    # ... rest unchanged
```

### 4. Update `render_tasks()` — Pass `on_toggled` Correctly

In `MainWindow.render_tasks()`, the `on_toggled` lambda currently passes `checked`:
```python
on_toggled=lambda checked, t=task: self.toggle_task(t, checked),
```
This is still valid since the click sends `True` (it's always a "check" action). Keep unchanged.

### 5. Update `_append_task_row_widget()` — Same Change

The `on_toggled` lambda is already there, no change needed.

---

## Code Quality
- **Minimal diff:** Remove checkbox widget and its references, don't restructure unrelated code
- **Backward compatible:** `on_toggled` signature unchanged — still receives `True` on click
- **More text space:** Removing checkbox gives ~28px more width to text column
- **Edit button still accessible:** Click on Edit button still triggers edit, not toggle

## Verification
- No checkbox visible on any task row
- Click a task → it sends to history (as before)
- Click Edit button → edit mode activates (not sent to history)
- Right-click → context menu works
- Groups indent still works
- At minimum width, all available space goes to text (no wasted checkbox space)