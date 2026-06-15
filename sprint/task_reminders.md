# Task-Specific Reminders

## Objective
Add a "Set Reminder" option to each task's context menu. When the reminder fires, the tray notification shows the task text.

## Implementation

### Step 1 — Add `reminderAt` field to task dict

In `src/backend/input_parser.py`, the task dict is created at lines 20-26. No change needed here — `reminderAt` is optional and only set via the context menu.

Task dict model (for reference):
```python
{
    "id": str(uuid.uuid4()),
    "text": "Buy groceries",
    "done": False,
    "createdAt": "2025-06-15T10:30:00",
    "reminderAt": "2025-06-15T14:00:00",       # optional, ISO timestamp
    "reminderFired": False,                      # optional, tracks if notification was shown
    "reminderRepeat": 30,                        # optional, repeat every N minutes
}
```

### Step 2 — Add reminder checker to MainWindow

In `MainWindow.__init__` (after `self._timer_manager` setup at line ~1618):

```python
# Task reminder checker — runs every 15 seconds
self._task_reminder_timer = QTimer(self)
self._task_reminder_timer.timeout.connect(self._check_task_reminders)
self._task_reminder_timer.start(15_000)
```

Add the checker method:

```python
def _check_task_reminders(self):
    """Check all tasks for pending reminders and fire notifications."""
    from datetime import datetime
    now = datetime.now()
    now_ts = now.timestamp()
    found = False
    for task in self.tasks:
        reminder_str = task.get("reminderAt")
        if not reminder_str or task.get("reminderFired", False):
            continue
        try:
            reminder_dt = datetime.fromisoformat(reminder_str)
        except (ValueError, TypeError):
            continue
        if now >= reminder_dt:
            task_text = task.get("text", "Task reminder")
            msg = f"Reminder: {task_text}"
            self._tray.show_message("Nudge", msg)
            task["reminderFired"] = True
            repeat = task.get("reminderRepeat", 0)
            if repeat > 0:
                # Reschedule for next interval
                from datetime import timedelta
                next_dt = reminder_dt + timedelta(minutes=repeat)
                task["reminderAt"] = next_dt.isoformat()
                task["reminderFired"] = False
            else:
                # One-time reminder, remove the field
                task.pop("reminderAt", None)
                task.pop("reminderFired", None)
                task.pop("reminderRepeat", None)
            found = True
    if found:
        self.store.save(self.tasks)
```

### Step 3 — Add "Set Reminder" to task context menu

Find `show_task_context_menu` (line 2499). Add after the Copy action (after line 2509):

```python
menu.addSeparator()

reminder_menu = menu.addMenu("Set Reminder")
remind_15m = QAction("15 minutes", self)
remind_15m.triggered.connect(lambda: self._set_task_reminder(task_ref, 15, repeat=0))
reminder_menu.addAction(remind_15m)
remind_30m = QAction("30 minutes", self)
remind_30m.triggered.connect(lambda: self._set_task_reminder(task_ref, 30, repeat=0))
reminder_menu.addAction(remind_30m)
remind_1h = QAction("1 hour", self)
remind_1h.triggered.connect(lambda: self._set_task_reminder(task_ref, 60, repeat=0))
reminder_menu.addAction(remind_1h)
remind_2h = QAction("2 hours", self)
remind_2h.triggered.connect(lambda: self._set_task_reminder(task_ref, 120, repeat=0))
reminder_menu.addAction(remind_2h)
remind_tomorrow = QAction("Tomorrow 9:00 AM", self)
remind_tomorrow.triggered.connect(lambda: self._set_task_reminder_at_time(task_ref, "09:00", days_ahead=1))
reminder_menu.addAction(remind_tomorrow)
reminder_menu.addSeparator()
remind_custom = QAction("Custom...", self)
remind_custom.triggered.connect(lambda: self._show_custom_reminder_dialog(task_ref))
reminder_menu.addAction(remind_custom)

# If task already has a reminder, show "Clear Reminder"
if task_ref.get("reminderAt") and not task_ref.get("reminderFired", False):
    clear_reminder = QAction("Clear Reminder", self)
    clear_reminder.triggered.connect(lambda: self._clear_task_reminder(task_ref))
    reminder_menu.addAction(clear_reminder)
```

### Step 4 — Add reminder helper methods

```python
def _set_task_reminder(self, task_ref, minutes_from_now: int, repeat: int = 0):
    """Set a one-time or repeating reminder on a task."""
    from datetime import datetime, timedelta
    reminder_dt = datetime.now() + timedelta(minutes=minutes_from_now)
    task_ref["reminderAt"] = reminder_dt.isoformat()
    task_ref["reminderFired"] = False
    if repeat > 0:
        task_ref["reminderRepeat"] = repeat
    else:
        task_ref.pop("reminderRepeat", None)
    self.store.save(self.tasks)

def _set_task_reminder_at_time(self, task_ref, time_str: str, days_ahead: int = 0):
    """Set reminder to a specific time (HH:MM) optionally days ahead."""
    from datetime import datetime, timedelta
    now = datetime.now()
    parts = time_str.split(":")
    target = now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0, microsecond=0)
    if days_ahead > 0:
        target += timedelta(days=days_ahead)
    if target <= now:
        target += timedelta(days=1)
    task_ref["reminderAt"] = target.isoformat()
    task_ref["reminderFired"] = False
    task_ref.pop("reminderRepeat", None)
    self.store.save(self.tasks)

def _clear_task_reminder(self, task_ref):
    """Remove a pending reminder from a task."""
    task_ref.pop("reminderAt", None)
    task_ref.pop("reminderFired", None)
    task_ref.pop("reminderRepeat", None)
    self.store.save(self.tasks)

def _show_custom_reminder_dialog(self, task_ref):
    """Dialog with QDateTimeEdit and optional repeat spinbox."""
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QDateTimeEdit, QSpinBox, QCheckBox, QPushButton,
    )
    from PyQt6.QtCore import QDateTime, Qt

    dlg = QDialog(self)
    dlg.setWindowTitle("Set Reminder")
    dlg.setFixedSize(340, 200)
    dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
    dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    # Apply theme
    theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
    theme = get_theme(theme_id)
    dlg.setStyleSheet(f"""
        QDialog {{ background: {theme["colors"]["windowBg"]}; }}
        QLabel {{ color: {theme["colors"]["text"]}; }}
        QPushButton {{ background: {theme["colors"]["accent"]}; color: {theme["colors"]["buttonText"]};
                       border: none; padding: 6px 14px; border-radius: 4px; }}
    """)

    layout = QVBoxLayout(dlg)
    layout.setSpacing(10)

    layout.addWidget(QLabel("Remind me at:"))

    dt_edit = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
    dt_edit.setCalendarPopup(True)
    dt_edit.setMinimumDateTime(QDateTime.currentDateTime())
    layout.addWidget(dt_edit)

    repeat_cb = QCheckBox("Repeat every")
    layout.addWidget(repeat_cb)

    repeat_row = QHBoxLayout()
    repeat_spin = QSpinBox()
    repeat_spin.setRange(1, 1440)
    repeat_spin.setValue(30)
    repeat_spin.setSuffix(" minutes")
    repeat_spin.setEnabled(False)
    repeat_cb.toggled.connect(repeat_spin.setEnabled)
    repeat_row.addWidget(repeat_spin)
    repeat_row.addStretch()
    layout.addLayout(repeat_row)

    btn_row = QHBoxLayout()
    btn_row.addStretch()
    cancel_btn = QPushButton("Cancel")
    cancel_btn.clicked.connect(dlg.reject)
    btn_row.addWidget(cancel_btn)
    ok_btn = QPushButton("Set")
    ok_btn.clicked.connect(dlg.accept)
    btn_row.addWidget(ok_btn)
    layout.addLayout(btn_row)

    if dlg.exec():
        qdt = dt_edit.dateTime()
        reminder_dt = qdt.toPyDateTime()
        task_ref["reminderAt"] = reminder_dt.isoformat()
        task_ref["reminderFired"] = False
        if repeat_cb.isChecked():
            task_ref["reminderRepeat"] = repeat_spin.value()
        else:
            task_ref.pop("reminderRepeat", None)
        self.store.save(self.tasks)
```

### Step 5 — Add import at top if not present

`from datetime import datetime` should already be imported at line 2 of `main_window.py`.

### Step 6 — Clean up on task deletion

In `delete_task` method, no extra work needed — deleting the task removes it from `self.tasks`, so `_check_task_reminders` won't see it anymore.

## Verification
1. Right-click a task → "Set Reminder" submenu appears
2. Select "15 minutes" → 15 min later, tray notification with task text
3. Right-click a task with pending reminder → "Clear Reminder" option shown
4. Clear it → no notification fires
5. Select "Custom..." → dialog with date/time picker + repeat checkbox
6. Set a recurring reminder → notification fires, then repeats at interval
7. Restart app — pending reminders persist in tasks.json
8. Light and dark themes both work