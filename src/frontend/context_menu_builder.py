from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable

from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QAction, QCursor, QFont
from PyQt6.QtWidgets import QApplication, QMenu, QWidget

from src.backend.task_groups import sorted_groups
from src.frontend.theme import get_theme, menu_stylesheet, normalize_theme_id

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class MenuContext:
    """Bundles the attributes ContextMenuBuilder needs from MainWindow."""
    app_state: dict
    timer_manager: Any
    groups_data: dict
    bold_font: Callable[[], QFont]
    main_widget: QWidget
    # Task action callbacks
    on_edit_task: Callable[[dict], None]
    on_delete_task: Callable[[dict], None]
    on_set_reminder: Callable[[dict, int], None]
    on_set_reminder_at_time: Callable[[dict, str, int], None]
    on_clear_reminder: Callable[[dict], None]
    on_show_custom_reminder: Callable[[dict], None]
    on_set_due_date: Callable[[dict, str], None]
    on_clear_due_date: Callable[[dict], None]
    on_show_custom_due_date: Callable[[dict], None]
    on_set_priority: Callable[[dict, str], None]
    on_clear_priority: Callable[[dict], None]
    on_set_recurrence: Callable[[dict, str, int], None]
    on_clear_recurrence: Callable[[dict], None]
    on_show_custom_recurrence: Callable[[dict], None]
    on_move_to_top: Callable[[dict], None]
    on_move_to_bottom: Callable[[dict], None]
    on_move_to_group: Callable[[dict, str], None]
    # App-level callbacks
    on_open_settings: Callable[[], None]
    on_toggle_always_on_top: Callable[[bool], None]
    on_toggle_pin: Callable[[bool], None]
    on_clear_completed: Callable[[], None]
    on_close: Callable[[], None]
    style_menu: Callable[..., Any]


class ContextMenuBuilder:
    """Builds the task context menu and app context menu."""

    def __init__(self, ctx: MenuContext) -> None:
        self._ctx = ctx

    def _bold_font(self):
        """Return a bold font for menu indicators."""
        return self._ctx.bold_font()

    def _style_context_menu(self, menu: QMenu) -> None:
        self._ctx.style_menu(menu)

    def show_task_context_menu(self, task_ref):
        parent = self._ctx.main_widget
        menu = QMenu(parent)
        self._style_context_menu(menu)

        edit_action = QAction("Edit", parent)
        edit_action.triggered.connect(lambda: self._ctx.on_edit_task(task_ref))
        menu.addAction(edit_action)

        copy_action = QAction("Copy", parent)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(task_ref.get("text", "")))
        menu.addAction(copy_action)

        menu.addSeparator()

        # Set Reminder submenu
        reminder_menu = menu.addMenu("Set Reminder")
        remind_1m = QAction("1 minutes", parent)
        remind_1m.triggered.connect(lambda: self._ctx.on_set_reminder(task_ref, 1))
        reminder_menu.addAction(remind_1m)
        remind_5m = QAction("5 minutes", parent)
        remind_5m.triggered.connect(lambda: self._ctx.on_set_reminder(task_ref, 5))
        reminder_menu.addAction(remind_5m)
        remind_15m = QAction("15 minutes", parent)
        remind_15m.triggered.connect(lambda: self._ctx.on_set_reminder(task_ref, 15))
        reminder_menu.addAction(remind_15m)
        remind_30m = QAction("30 minutes", parent)
        remind_30m.triggered.connect(lambda: self._ctx.on_set_reminder(task_ref, 30))
        reminder_menu.addAction(remind_30m)
        remind_1h = QAction("1 hour", parent)
        remind_1h.triggered.connect(lambda: self._ctx.on_set_reminder(task_ref, 60))
        reminder_menu.addAction(remind_1h)
        remind_2h = QAction("2 hours", parent)
        remind_2h.triggered.connect(lambda: self._ctx.on_set_reminder(task_ref, 120))
        reminder_menu.addAction(remind_2h)
        remind_tomorrow = QAction("Tomorrow 9:00 AM", parent)
        remind_tomorrow.triggered.connect(lambda: self._ctx.on_set_reminder_at_time(task_ref, "09:00", days_ahead=1))
        reminder_menu.addAction(remind_tomorrow)
        reminder_menu.addSeparator()
        remind_custom = QAction("Custom...", parent)
        remind_custom.triggered.connect(lambda: self._ctx.on_show_custom_reminder(task_ref))
        reminder_menu.addAction(remind_custom)
        if self._ctx.timer_manager.get_timer_for_task(task_ref["id"]) is not None:
            clear_reminder = QAction("Clear Reminder", parent)
            clear_reminder.triggered.connect(lambda: self._ctx.on_clear_reminder(task_ref))
            reminder_menu.addAction(clear_reminder)

        # Set Due Date submenu
        due_date_menu = menu.addMenu("Set Due Date")
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        current_due = task_ref.get("dueDate")

        due_today = QAction("Today", parent)
        if current_due == today:
            due_today.setFont(self._bold_font())
        due_today.triggered.connect(lambda: self._ctx.on_set_due_date(task_ref, today))
        due_date_menu.addAction(due_today)

        due_tomorrow = QAction("Tomorrow", parent)
        if current_due == tomorrow:
            due_tomorrow.setFont(self._bold_font())
        due_tomorrow.triggered.connect(lambda: self._ctx.on_set_due_date(task_ref, tomorrow))
        due_date_menu.addAction(due_tomorrow)

        due_next_week = QAction("Next Week", parent)
        if current_due == next_week:
            due_next_week.setFont(self._bold_font())
        due_next_week.triggered.connect(lambda: self._ctx.on_set_due_date(task_ref, next_week))
        due_date_menu.addAction(due_next_week)

        due_date_menu.addSeparator()

        due_custom = QAction("Custom...", parent)
        due_custom.triggered.connect(lambda: self._ctx.on_show_custom_due_date(task_ref))
        due_date_menu.addAction(due_custom)

        if current_due is not None:
            clear_due = QAction("Clear Due Date", parent)
            clear_due.triggered.connect(lambda: self._ctx.on_clear_due_date(task_ref))
            due_date_menu.addAction(clear_due)

        # Set Priority submenu
        priority_menu = menu.addMenu("Set Priority")
        current_priority = task_ref.get("priority")

        pri_high = QAction("High", parent)
        if current_priority == "high":
            pri_high.setFont(self._bold_font())
        pri_high.triggered.connect(lambda: self._ctx.on_set_priority(task_ref, "high"))
        priority_menu.addAction(pri_high)

        if current_priority is not None:
            clear_pri = QAction("Clear Priority", parent)
            clear_pri.triggered.connect(lambda: self._ctx.on_clear_priority(task_ref))
            priority_menu.addAction(clear_pri)

        # Set Recurrence submenu
        recurrence_menu = menu.addMenu("Set Recurrence")
        current_recurrence = task_ref.get("recurrence")
        current_type = current_recurrence.get("type") if current_recurrence else None
        current_interval = current_recurrence.get("interval", 1) if current_recurrence else 1

        presets = [
            ("Daily", "daily", 1),
            ("Weekly", "weekly", 1),
            ("Monthly", "monthly", 1),
            ("Yearly", "yearly", 1),
            ("Every 2 Weeks", "weekly", 2),
            ("Every 2 Months", "monthly", 2),
        ]
        for label, rtype, interval in presets:
            action = QAction(label, parent)
            if current_type == rtype and current_interval == interval:
                action.setFont(self._bold_font())
            action.triggered.connect(
                lambda checked=False, t=task_ref, rt=rtype, iv=interval: self._ctx.on_set_recurrence(t, rt, iv)
            )
            recurrence_menu.addAction(action)

        recurrence_menu.addSeparator()

        custom_action = QAction("Custom...", parent)
        custom_action.triggered.connect(lambda: self._ctx.on_show_custom_recurrence(task_ref))
        recurrence_menu.addAction(custom_action)

        if current_recurrence is not None:
            clear_action = QAction("Clear Recurrence", parent)
            clear_action.triggered.connect(lambda: self._ctx.on_clear_recurrence(task_ref))
            recurrence_menu.addAction(clear_action)

        menu.addSeparator()

        move_top_action = QAction("Move to Top", parent)
        move_top_action.triggered.connect(lambda: self._ctx.on_move_to_top(task_ref))
        menu.addAction(move_top_action)

        move_bottom_action = QAction("Move to Bottom", parent)
        move_bottom_action.triggered.connect(lambda: self._ctx.on_move_to_bottom(task_ref))
        menu.addAction(move_bottom_action)

        menu.addSeparator()

        move_menu = menu.addMenu("Move to Group")
        for group in sorted_groups(self._ctx.groups_data):
            action = QAction(group["name"], parent)
            gid = group["id"]
            action.triggered.connect(lambda checked=False, g=gid: self._ctx.on_move_to_group(task_ref, g))
            move_menu.addAction(action)

        menu.addSeparator()

        delete_action = QAction("Delete", parent)
        delete_action.setObjectName("deleteAction")
        delete_action.triggered.connect(lambda: self._ctx.on_delete_task(task_ref))
        menu.addAction(delete_action)

        # Calculate menu height and clamp position to screen bounds
        pos = QCursor.pos()
        screen = QApplication.screenAt(pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        action_count = len(menu.actions())
        row_height = 28
        menu_height = action_count * row_height + 8
        menu_width = 200

        x = pos.x()
        if x + menu_width > screen_rect.right():
            x = screen_rect.right() - menu_width
        if x < screen_rect.left():
            x = screen_rect.left()

        y = pos.y()
        if y + menu_height > screen_rect.bottom():
            y = screen_rect.bottom() - menu_height
        if y < screen_rect.top():
            y = screen_rect.top()

        menu.exec(QPoint(x, y))

    def contextMenuEvent(self, event):
        parent = self._ctx.main_widget
        context_menu = QMenu(parent)
        self._style_context_menu(context_menu)

        settings_action = QAction("Settings", parent)
        settings_action.triggered.connect(self._ctx.on_open_settings)
        context_menu.addAction(settings_action)

        always_on_top_action = QAction("Always on Top", parent)
        always_on_top_action.setCheckable(True)
        always_on_top_action.setChecked(self._ctx.app_state.get("alwaysOnTop", False))
        always_on_top_action.triggered.connect(self._ctx.on_toggle_always_on_top)
        context_menu.addAction(always_on_top_action)

        pin_desktop_action = QAction("Pin to Desktop Background", parent)
        pin_desktop_action.setCheckable(True)
        pin_desktop_action.setChecked(self._ctx.app_state.get("pinnedToDesktop", False))
        pin_desktop_action.triggered.connect(self._ctx.on_toggle_pin)
        context_menu.addAction(pin_desktop_action)

        context_menu.addSeparator()

        clear_action = QAction("Clear Completed Tasks", parent)
        clear_action.triggered.connect(self._ctx.on_clear_completed)
        context_menu.addAction(clear_action)

        exit_action = QAction("Exit App", parent)
        exit_action.triggered.connect(self._ctx.on_close)
        context_menu.addAction(exit_action)

        context_menu.exec(event.globalPos())
