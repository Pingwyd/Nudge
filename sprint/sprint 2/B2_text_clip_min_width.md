# B2 — Fix Text Clipped at Minimum Width on First Insert

## Problem
When adding a new task at minimum window width (380×480), the text wraps poorly / gets clipped. Resizing the window fixes it.

## Root Cause
`_sync_task_list_viewport_width()` sets `tasks_widget.setMinimumWidth(viewport_w)` but this happens *after* the row is created. The new row's `ResponsiveTextRowHelper` calculates available width before the viewport width propagates.

## Files
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py`
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\responsive_text.py`

---

## Fix 1: Force Layout Update Before Row Creation

In `MainWindow._append_task_row_widget()` (around line 1597), **before** creating the row:

```python
def _append_task_row_widget(self, task: dict) -> TaskRowWidget:
    group_id = task.get("groupId", GENERAL_GROUP_ID)
    section = self.group_sections.get(group_id)
    if section is not None:
        group_tasks = tasks_for_group(self.tasks, group_id)
        
        # ENSURE VIEWPORT WIDTH IS SYNCED BEFORE ROW CREATION
        self._sync_task_list_viewport_width()
        QApplication.processEvents()  # Let layout settle
        
        fresh = StateManager("appstate.json")
        fresh.load()
        text_size = int(fresh.state.get("taskTextSize", 14))
        self.state_manager.state["taskTextSize"] = text_size
        self.task_text_size = text_size
        # ... rest unchanged
```

---

## Fix 2: ResponsiveTextRowHelper — Handle Zero/Min Width Gracefully

In `src/frontend/responsive_text.py`, `available_text_width()`:

```python
def available_text_width(host: QWidget, reserved: Iterable[QWidget]) -> int:
    layout = host.layout()
    if layout is None:
        return max(1, host.width())
    
    available = host.width()
    margins = layout.contentsMargins()
    available -= margins.left() + margins.right()
    
    reserved_set = set(reserved)
    widget_count = 0
    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item is None or item.widget() is None:
            continue
        widget_count += 1
        widget = item.widget()
        if widget in reserved_set:
            # Use sizeHint if width() is 0 (not laid out yet)
            w = widget.width() or widget.sizeHint().width()
            available -= w
    
    if widget_count > 1:
        available -= layout.spacing() * (widget_count - 1)
    
    # Never return less than a readable minimum
    return max(120, available)
```

---

## Fix 3: TaskRowWidget — Defer Sync Until Visible

In `TaskRowWidget.__init__`, don't call `sync_text_layout()` immediately. Instead, use `QTimer.singleShot(0, self.sync_text_layout)` after the widget is added to layout.

```python
def __init__(self, ...):
    # ... existing init ...
    # REMOVE: self.set_text_size(text_size)  -- keep but defer sync
    self.set_text_size(text_size)
    # Defer layout sync until widget is in layout hierarchy
    QTimer.singleShot(0, self.sync_text_layout)
```

---

## Code Quality
- **No hardcoded values:** Use `MIN_TEXT_COLUMN_WIDTH` constant (already 120)
- **Deferred layout:** `QTimer.singleShot(0, ...)` ensures widget is in layout tree
- **Defensive width:** `widget.width() or widget.sizeHint().width()` handles zero-width widgets
- **ProcessEvents:** Minimal use, only during task insertion to force layout pass

## Verification
- Set window to minimum size (380×480)
- Add task "Short task" → text visible, not clipped
- Add task "Very long task text that should wrap properly across multiple lines at minimum width" → wraps correctly
- Resize window → text reflows correctly (no regression)
- Edit mode at min width → editor width correct