# B3 — Fix Task Text Clipping When Editing

## Problem
When clicking "Edit" on a task, the `QLineEdit` editor clips text — doesn't show full content, especially at minimum width.

## Root Cause
`TaskRowWidget.begin_edit()` switches `content_stack` to editor page, but:
1. Editor width not recalculated for current row width
2. `fix_single_line_editor_height()` sets fixed height but width constraint missing
3. Stacked widget page switch doesn't trigger layout update on editor

## File
`C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py` — `TaskRowWidget` class

---

## Fix: Update `begin_edit()` and `commit_edit()`

### In `TaskRowWidget.begin_edit()`
```python
def begin_edit(self):
    if self._editing:
        return
    self._editing = True
    self.editor.setText(self.label.text())
    self.content_stack.setCurrentIndex(1)
    self.edit_btn.setText("Save")
    
    # FORCE EDITOR WIDTH RECALCULATION
    self.content_stack.updateGeometry()
    self.updateGeometry()
    self.sync_text_layout()  # This calls _sync_content_stack_height which fixes editor height
    
    # Ensure editor gets focus and selects all
    QTimer.singleShot(0, lambda: (
        self.editor.setFocus(),
        self.editor.selectAll()
    ))
```

### In `TaskRowWidget.commit_edit()`
```python
def commit_edit(self):
    if not self._editing:
        self.begin_edit()
        return

    new_text = self.editor.text().strip()
    if not new_text:
        self.editor.setFocus()
        self.editor.selectAll()
        return

    self.label.setText(new_text)
    self._editing = False
    self.content_stack.setCurrentIndex(0)
    self.edit_btn.setText("Edit")
    self.content_stack.updateGeometry()
    self.updateGeometry()
    
    if self.on_commit:
        self.on_commit(new_text)
    self.sync_text_layout()
```

### In `_sync_content_stack_height()` — Ensure Editor Width
```python
def _sync_content_stack_height(self):
    ht_reserved = [self.checkbox, self.edit_btn]
    if self._indent_spacer is not None:
        ht_reserved.insert(0, self._indent_spacer)
    column_width = available_text_width(self, ht_reserved)
    
    if self._editing:
        # Apply width constraint to editor BEFORE fixing height
        apply_editor_field_width(self.editor, column_width)
        fix_single_line_editor_height(self.editor)
        sync_stacked_page_height(self.content_stack, self.editor.height())
    else:
        sync_stacked_page_height(
            self.content_stack,
            label_content_height(self.label, column_width),
        )
```

---

## Code Quality
- **Reuse existing helpers:** `apply_editor_field_width`, `fix_single_line_editor_height`, `available_text_width`
- **Deferred focus:** `QTimer.singleShot(0, ...)` ensures editor is visible before focus
- **Geometry updates:** `updateGeometry()` on both stack and row propagates size hints
- **Single sync point:** `sync_text_layout()` handles both label and editor

## Verification
- Click Edit on short task at min width → editor shows full text
- Click Edit on long task → editor scrolls horizontally, full text accessible
- Type in editor → text doesn't clip
- Save → label updates, no layout shift
- Cancel (click away) → reverts correctly