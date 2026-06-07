# B7 — Min Width Text Spans Full Width to Edit Button

## Problem
At minimum window width (380×480), the task text column only uses ~3 words per line and doesn't stretch to the Edit button. There is wasted space on the right.

## Root Cause
`MIN_TEXT_COLUMN_WIDTH` in `responsive_text.py` is set to 120px, which caps the minimum text column. But at the app's minimum width (380px minus margins, scrollbar, Edit button, spacing), the available text width is actually larger than 120px. The cap prevents the text from using available space.

## Files
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\responsive_text.py`
- `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py`

---

## Fix 1: Increase `MIN_TEXT_COLUMN_WIDTH`

In `responsive_text.py`:
```python
# Change from 120 to 180 — allows better word wrapping at min width
MIN_TEXT_COLUMN_WIDTH = 180
```

## Fix 2: Make Minimum Width Dynamic in `apply_wrapped_text_width()`

```python
def apply_wrapped_text_width(label: QLabel, available_width: int) -> None:
    """Set width constraints so wrap reflows; prefer at least MIN_TEXT_COLUMN_WIDTH."""
    width = max(1, available_width)
    label.setMaximumWidth(width)
    # Use a percentage of available width as minimum, not a hardcoded constant
    min_width = min(width, int(available_width * 0.4))
    min_width = max(min_width, MIN_TEXT_COLUMN_WIDTH)
    label.setMinimumWidth(min_width)
    label.adjustSize()
```

## Fix 3: Ensure Tasks Widget Minimum Width Matches Viewport

In `_sync_task_list_viewport_width()`:
```python
def _sync_task_list_viewport_width(self) -> None:
    """Rows span the scroll viewport so Edit can sit on the window's right edge."""
    if self.scroll_area is None or self.tasks_widget is None:
        return
    viewport_w = self.scroll_area.viewport().width()
    if viewport_w > 0:
        # Account for scroll bar width when visible
        scrollbar_w = self.scroll_area.verticalScrollBar().width() if self.scroll_area.verticalScrollBar().isVisible() else 0
        effective_w = viewport_w - scrollbar_w
        self.tasks_widget.setMinimumWidth(effective_w)
```

## Fix 4: Reduce Layout Margins at Minimum Width

In `MainWindow.init_ui()`, the layout margins are currently 15px on all sides. Consider reducing at minimum width:

```python
# In init_ui() or resizeEvent():
layout.setContentsMargins(15, 15, 15, 15)
# Could adjust based on width:
# margin = max(8, min(15, self.width() // 30))
```

(Optional — only if needed after Fixes 1-3)

---

## Code Quality
- **Percentage-based minimum:** `40%` of available width ensures dynamic behavior across sizes
- **Fail-safe:** `max(min_width, MIN_TEXT_COLUMN_WIDTH)` never goes below minimum readable
- **Scroll bar compensation:** Accounts for scrollbar visibility
- **No hardcoded widths:** Only the constant `MIN_TEXT_COLUMN_WIDTH` is changed

## Verification
- Resize window to minimum (380×480)
- Short task: text spans from left icon area to Edit button
- Long task: wraps in wider lines (not 3-word columns)
- No text clipped on right side
- Resize wider → text reflows normally
- Edit mode: editor width matches text area width at all sizes