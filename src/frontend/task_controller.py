from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable

from PyQt6.QtCore import QPoint, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QCheckBox, QComboBox, QDateEdit, \
    QDialog, QFrame, QLabel, QLineEdit, QMenu, QPushButton, QScrollArea, \
    QSpinBox, QTimeEdit, QVBoxLayout, QWidget

from src.backend.defaults import DEFAULT_GROUPS_ENABLED
from src.backend.input_parser import InputParser
from src.backend.recurrence_manager import RecurrenceManager
from src.backend.state_manager import StateManager
from src.backend.task_groups import (GENERAL_GROUP_ID, sorted_groups,
                                    tasks_for_group,
                                    rebuild_tasks_preserving_groups)
from src.constants import RENDER_DEBOUNCE_MS, ROW_POOL_MAX
from src.frontend.task_row import TaskRowWidget
from src.frontend.theme import get_theme, normalize_theme_id
from src.frontend.themed_message_dialog import ThemedMessageDialog
from src.frontend.undo_toast import UndoToast
from src.frontend.widget_context import WidgetContext

if TYPE_CHECKING:
    from src.frontend.task_group_section import TaskGroupSection

logger = logging.getLogger(__name__)


@dataclass
class TaskContext:
    """Bundles the attributes TaskController needs from MainWindow."""
    tasks: list[dict]
    store: Any  # TaskStore
    history_store: Any  # HistoryStore
    group_store: Any  # GroupStore
    app_state: dict
    state_manager: Any  # StateManager
    timer_manager: Any  # TimerManager
    widget_context: WidgetContext
    tasks_layout: QVBoxLayout
    tasks_widget: QWidget
    scroll_area: QScrollArea
    task_row_widgets: dict  # id -> TaskRowWidget
    group_sections: dict  # group_id -> TaskGroupSection
    groups_data: dict
    input_bar: Any  # QLineEdit
    flat_drop_indicator: Any  # QFrame
    group_drop_indicator: Any  # QFrame
    flat_drag_hover_index: int = -1
    last_archived_task: dict | None = None
    active_undo_toast: Any = None
    history_dialog: Any = None
    group_combo: Any = None
    main_window: Any = None
    sound_manager: Any = None
    # Callbacks into MainWindow
    on_render_tasks: Callable[[], None] | None = None
    on_update_empty_state: Callable[[], None] | None = None
    on_update_tag_filter: Callable[[], None] | None = None
    on_apply_tag_filter: Callable[[], None] | None = None
    on_apply_search_filter: Callable[[], None] | None = None
    on_sync_viewport_width: Callable[[], None] | None = None
    on_sync_row_text_layouts: Callable[[], None] | None = None
    on_enable_resize_hover: Callable[[QWidget], None] | None = None
    on_show_context_menu: Callable[[dict], None] | None = None
    # Group-related callbacks for render_tasks
    on_save_group_expanded: Callable[[str, bool], None] | None = None
    on_show_group_header_menu: Callable[[str, object], None] | None = None
    on_select_active_group: Callable[[str], None] | None = None


class TaskController:
    def __init__(self, ctx: TaskContext):
        self._ctx = ctx
        self._widget_pool: list = []
        self._render_timer = QTimer()
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(RENDER_DEBOUNCE_MS)
        self._render_timer.timeout.connect(self._do_render)

    # ------------------------------------------------------------------
    # Task creation
    # ------------------------------------------------------------------

    def process_input(self) -> None:
        raw_text = self._ctx.input_bar.text()
        if not raw_text.strip():
            return

        new_tasks = InputParser.parse_input(raw_text)
        group_id = self._current_input_group_id()
        for task in new_tasks:
            task["groupId"] = group_id
        self._ctx.tasks.extend(new_tasks)
        self._ctx.input_bar.clear()

        self._ctx.store.save(self._ctx.tasks)
        last_row = None
        for task in new_tasks:
            last_row = self._append_task_row_widget(task)
        if last_row is not None and self._ctx.scroll_area is not None:
            QTimer.singleShot(0, lambda r=last_row: self._ctx.scroll_area.ensureWidgetVisible(r, 0, 80))

    def _current_input_group_id(self) -> str:
        if self._ctx.group_combo is not None:
            group_id = self._ctx.group_combo.currentData()
            return group_id if group_id else GENERAL_GROUP_ID
        return GENERAL_GROUP_ID

    # ------------------------------------------------------------------
    # Clipboard import
    # ------------------------------------------------------------------

    def import_from_clipboard(self) -> int:
        """Import tasks from clipboard text (one task per line).

        Returns the number of tasks imported, or 0 if nothing was imported.
        """
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        if clipboard is None:
            return 0

        mime = clipboard.mimeData()
        if mime is None or not mime.hasText():
            return 0

        text = mime.text()
        if not text or not text.strip():
            return 0

        lines = text.split("\n")
        group_id = self._current_input_group_id()
        new_tasks = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            parsed = InputParser.parse_input(stripped)
            for task in parsed:
                task["groupId"] = group_id
            new_tasks.extend(parsed)

        if not new_tasks:
            return 0

        self._ctx.tasks.extend(new_tasks)
        self._ctx.store.save(self._ctx.tasks)

        last_row = None
        for task in new_tasks:
            last_row = self._append_task_row_widget(task)
        if last_row is not None and self._ctx.scroll_area is not None:
            QTimer.singleShot(0, lambda r=last_row: self._ctx.scroll_area.ensureWidgetVisible(r, 0, 80))

        return len(new_tasks)

    # ------------------------------------------------------------------
    # Drag-and-drop import
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip HTML tags, returning plain text.

        For anchor tags, prefer the href URL over the link text.
        """
        import re
        # Extract URLs from anchor tags first
        anchors = re.findall(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE)
        if anchors:
            # Use the URL if the text is just the URL repeated, otherwise use the URL
            parts = []
            for href, text in anchors:
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                if clean_text and clean_text != href:
                    parts.append(clean_text)
                else:
                    parts.append(href)
            if parts:
                return " ".join(parts)
        # Fallback: strip all tags
        clean = re.sub(r'<[^>]+>', '', html)
        return clean.strip()

    @staticmethod
    def _filename_stem(path: str) -> str:
        """Extract filename without extension from a path."""
        import os
        base = os.path.basename(path)
        stem, _ = os.path.splitext(base)
        return stem.strip()

    def create_tasks_from_drop(self, items: list[dict]) -> None:
        """Create tasks from external drag-and-drop items.

        Each item is {"type": "text"|"html"|"file", "content": str}.
        """
        from datetime import datetime
        import uuid

        group_id = self._current_input_group_id()
        new_tasks = []

        for item in items:
            kind = item.get("type", "text")
            content = item.get("content", "")

            if kind == "html":
                text = self._strip_html(content)
            elif kind == "file":
                text = self._filename_stem(content)
            else:
                text = content.strip()

            if not text:
                continue

            task = {
                "id": str(uuid.uuid4()),
                "text": text,
                "done": False,
                "createdAt": datetime.now().isoformat(),
                "order": 0,
                "dueDate": None,
                "priority": None,
                "tags": [],
                "recurrence": None,
                "groupId": group_id,
            }
            new_tasks.append(task)

        if not new_tasks:
            return

        self._ctx.tasks.extend(new_tasks)
        self._ctx.store.save(self._ctx.tasks)

        last_row = None
        for task in new_tasks:
            last_row = self._append_task_row_widget(task)
        if last_row is not None and self._ctx.scroll_area is not None:
            QTimer.singleShot(0, lambda r=last_row: self._ctx.scroll_area.ensureWidgetVisible(r, 0, 80))

    # ------------------------------------------------------------------
    # Widget pool
    # ------------------------------------------------------------------

    def _acquire_row(self, task, text_size, content_indent, toggle_cb, commit_cb, context_menu_cb):
        """Get a TaskRowWidget from the pool or create new."""
        font_name = self._ctx.state_manager.state.get("taskFont", "Default (System)")
        if self._widget_pool:
            row = self._widget_pool.pop()
        else:
            # Parent immediately so the row never becomes a top-level window.
            row = TaskRowWidget(
                task["text"],
                checked=task.get("done", False),
                text_size=text_size,
                on_toggled=toggle_cb,
                on_commit=commit_cb,
                on_context_menu=context_menu_cb,
                content_indent=content_indent,
                parent=self._ctx.tasks_widget,
            )
            row.hide()
            row._ctx = self._ctx.widget_context
        # Visibility filters hide rows with no _task_ref; bind on create and reuse.
        row.update_task(
            task,
            on_toggled=toggle_cb,
            on_commit=commit_cb,
            on_context_menu=context_menu_cb,
        )
        row.set_text_size(text_size, sync=False)
        if hasattr(row, "set_task_font"):
            row.set_task_font(font_name, sync=False)
        return row

    def _release_all_rows(self):
        """Return all tracked rows to the pool (hidden, still parented)."""
        for row in self._ctx.task_row_widgets.values():
            row.hide()
            # Do not setParent(None): that promotes the row to a top-level
            # window and briefly paints ghost frames on Windows/DWM.
            self._widget_pool.append(row)
        self._ctx.task_row_widgets.clear()

    # ------------------------------------------------------------------
    # Debounced render
    # ------------------------------------------------------------------

    def render_tasks(self, force=False):
        """Public API — debounced unless force=True."""
        if force:
            self._render_timer.stop()
            self._do_render()
        else:
            self.schedule_render()

    def schedule_render(self):
        """Debounced render — batches rapid state changes."""
        if not self._render_timer.isActive():
            self._render_timer.start()

    def _do_render(self) -> None:
        from src.frontend.priority_header import PriorityHeaderWidget
        from src.frontend.task_group_section import TaskGroupSection

        self._ctx.tasks_widget.setUpdatesEnabled(False)

        # Collect existing row widgets into pool
        old_widgets = []
        while self._ctx.tasks_layout.count():
            child = self._ctx.tasks_layout.takeAt(0)
            w = child.widget() if child else None
            if w is not None:
                old_widgets.append(w)

        self._release_all_rows()

        # Delete non-TaskRowWidget items (headers, sections, stretch)
        for w in old_widgets:
            if not isinstance(w, TaskRowWidget):
                w.deleteLater()

        self._ctx.group_sections.clear()

        text_size = int(self._ctx.state_manager.state.get("taskTextSize", 14))
        groups_enabled = self._ctx.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)
        theme_id = normalize_theme_id(self._ctx.app_state.get("theme", "dark"))

        if not groups_enabled:
            self._ctx.tasks_widget.setAcceptDrops(True)

            high_tasks = [t for t in self._ctx.tasks if t.get("priority") == "high"]
            normal_tasks = [t for t in self._ctx.tasks if t.get("priority") != "high"]

            if high_tasks:
                header = PriorityHeaderWidget(
                    theme_id=theme_id, parent=self._ctx.tasks_widget
                )
                self._ctx.tasks_layout.addWidget(header, 0, Qt.AlignmentFlag.AlignTop)

            for task in high_tasks:
                row = self._acquire_row(
                    task, text_size, 0,
                    lambda checked, t=task: self.toggle_task(t, checked),
                    lambda new_text, t=task: self.update_task_text(t, new_text),
                    lambda global_pos, t=task: self._show_task_context_menu_at(t, global_pos),
                )
                self._ctx.tasks_layout.addWidget(row, 0, Qt.AlignmentFlag.AlignTop)
                self._ctx.task_row_widgets[id(task)] = row

            if high_tasks and normal_tasks:
                row._is_section_end = True
                row.update()

            for task in normal_tasks:
                row = self._acquire_row(
                    task, text_size, 0,
                    lambda checked, t=task: self.toggle_task(t, checked),
                    lambda new_text, t=task: self.update_task_text(t, new_text),
                    lambda global_pos, t=task: self._show_task_context_menu_at(t, global_pos),
                )
                self._ctx.tasks_layout.addWidget(row, 0, Qt.AlignmentFlag.AlignTop)
                self._ctx.task_row_widgets[id(task)] = row
        else:
            self._ctx.tasks_widget.setAcceptDrops(False)
            for group in sorted_groups(self._ctx.groups_data):
                group_id = group["id"]
                group_tasks = tasks_for_group(self._ctx.tasks, group_id)
                section = TaskGroupSection(
                    group,
                    len(group_tasks),
                    text_size=14,
                    on_toggle_expanded=self._ctx.on_save_group_expanded,
                    on_header_context_menu=self._ctx.on_show_group_header_menu,
                    on_header_clicked=self._ctx.on_select_active_group,
                    parent=self._ctx.tasks_widget,
                )
                for task in group_tasks:
                    row = self._acquire_row(
                        task, text_size, 8,
                        lambda checked, t=task: self.toggle_task(t, checked),
                        lambda new_text, t=task: self.update_task_text(t, new_text),
                        lambda global_pos, t=task: self._show_task_context_menu_at(t, global_pos),
                    )
                    section.add_task_row(row)
                    self._ctx.task_row_widgets[id(task)] = row
                section._ctx = self._ctx.widget_context
                section.refresh_header_count()
                self._ctx.tasks_layout.addWidget(section, 0, Qt.AlignmentFlag.AlignTop)
                self._ctx.group_sections[group_id] = section

        self._ctx.tasks_layout.addStretch(1)

        # Keep a bounded pool for the next render instead of destroying every spare row.
        keep = max(ROW_POOL_MAX, len(self._ctx.task_row_widgets))
        while len(self._widget_pool) > keep:
            row = self._widget_pool.pop()
            row.hide()
            row.deleteLater()

        self._ctx.on_sync_viewport_width()
        self._ctx.on_sync_row_text_layouts()
        self._ctx.flat_drop_indicator.raise_()
        self._ctx.group_drop_indicator.raise_()
        self._ctx.tasks_widget.setUpdatesEnabled(True)
        self._ctx.on_update_empty_state()
        self._ctx.on_update_tag_filter()
        # Tag + search visibility share one path; calling either is enough.
        if self._ctx.on_apply_search_filter is not None:
            self._ctx.on_apply_search_filter()
        elif self._ctx.on_apply_tag_filter is not None:
            self._ctx.on_apply_tag_filter()

        if self._ctx.on_enable_resize_hover is not None:
            self._ctx.on_enable_resize_hover(self._ctx.tasks_widget.parentWidget())

    def _recalculate_section_dividers(self):
        """Recalculate which row is the last high-priority task (gets thick divider)."""
        groups_enabled = self._ctx.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)

        if not groups_enabled:
            tasks = self._ctx.tasks
            high_tasks = [t for t in tasks if t.get("priority") == "high" and not t.get("done")]
            last_high_id = id(high_tasks[-1]) if high_tasks else None
            for task in tasks:
                row = self._ctx.task_row_widgets.get(id(task))
                if row is None:
                    continue
                was_end = row._is_section_end
                row._is_section_end = (id(task) == last_high_id and bool(high_tasks))
                if was_end != row._is_section_end:
                    row.update()
        else:
            for group_id, section in self._ctx.group_sections.items():
                last_high_row = None
                for row in section.task_rows:
                    task = getattr(row, "_task_ref", None)
                    if task and task.get("priority") == "high" and not task.get("done"):
                        last_high_row = row
                for row in section.task_rows:
                    was_end = row._is_section_end
                    row._is_section_end = (row is last_high_row)
                    if was_end != row._is_section_end:
                        row.update()

    # ------------------------------------------------------------------
    # Row widget management
    # ------------------------------------------------------------------

    def _append_task_row_widget(self, task: dict) -> TaskRowWidget | None:
        self._ctx.on_sync_viewport_width()
        groups_enabled = self._ctx.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)
        text_size = int(self._ctx.state_manager.state.get("taskTextSize", 14))
        self._ctx.state_manager.state["taskTextSize"] = text_size
        row = TaskRowWidget(
            task["text"],
            checked=task.get("done", False),
            text_size=text_size,
            on_toggled=lambda checked, t=task: self.toggle_task(t, checked),
            on_commit=lambda new_text, t=task: self.update_task_text(t, new_text),
            on_context_menu=lambda global_pos, t=task: self._show_task_context_menu_at(t, global_pos),
            content_indent=0 if not groups_enabled else 8,
            parent=self._ctx.tasks_widget,
        )
        row.hide()
        font_name = self._ctx.state_manager.state.get("taskFont", "Default (System)")
        if hasattr(row, "set_task_font"):
            row.set_task_font(font_name, sync=False)
        if not groups_enabled:
            is_high = task.get("priority") == "high"
            # Scan layout to find the correct insert position.
            # Layout order: [header?] [high rows...] [divider?] [normal rows...] [stretch]
            layout = self._ctx.tasks_layout
            insert_idx = layout.count() - 1  # default: before stretch

            if is_high:
                # Insert after the last high-priority row, or after header
                last_high_idx = -1
                for i in range(layout.count()):
                    w = layout.itemAt(i).widget()
                    if w is None:
                        continue
                    from src.frontend.priority_header import PriorityHeaderWidget
                    if isinstance(w, PriorityHeaderWidget):
                        last_high_idx = i
                    elif hasattr(w, '_task_ref') and w._task_ref.get("priority") == "high":
                        last_high_idx = i
                insert_idx = last_high_idx + 1 if last_high_idx >= 0 else 0
            else:
                # Insert after the last high-priority row
                for i in range(layout.count()):
                    w = layout.itemAt(i).widget()
                    if w is None:
                        continue
                    if hasattr(w, '_task_ref') and w._task_ref.get("priority") == "high":
                        insert_idx = i + 1

            self._ctx.tasks_layout.insertWidget(insert_idx, row, 0, Qt.AlignmentFlag.AlignTop)
            if is_high:
                self._sync_priority_header()
        else:
            group_id = task.get("groupId", GENERAL_GROUP_ID)
            section = self._ctx.group_sections.get(group_id)
            if section is None:
                row.setParent(None)
                row.deleteLater()
                return None
            group_tasks = tasks_for_group(self._ctx.tasks, group_id)
            insert_index = len(group_tasks) - 1
            section.add_task_row(row, index=insert_index)
            section.refresh_header_count()
        row._ctx = self._ctx.widget_context
        row.set_task_ref(task)
        self._ctx.task_row_widgets[id(task)] = row
        self._ctx.on_sync_viewport_width()
        self._ctx.on_sync_row_text_layouts()
        self._ctx.on_update_empty_state()
        self._ctx.on_update_tag_filter()
        if self._ctx.on_apply_search_filter is not None:
            self._ctx.on_apply_search_filter()
        elif self._ctx.on_apply_tag_filter is not None:
            self._ctx.on_apply_tag_filter()
        return row

    def _remove_task_row_widget(self, task: dict) -> None:
        row = self._ctx.task_row_widgets.pop(id(task), None)
        if row is None:
            return
        row._stop_countdown()
        groups_enabled = self._ctx.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)
        if groups_enabled:
            group_id = task.get("groupId", GENERAL_GROUP_ID)
            section = self._ctx.group_sections.get(group_id)
            if section is not None:
                section.remove_task_row(row)
                section.refresh_header_count()
        else:
            self._ctx.tasks_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
            self._sync_priority_header()
        self._ctx.on_sync_viewport_width()
        self._ctx.on_update_empty_state()

    def _sync_priority_header(self):
        """Add or remove PriorityHeaderWidget based on remaining high-priority tasks."""
        from src.frontend.priority_header import PriorityHeaderWidget
        has_high = any(t.get("priority") == "high" for t in self._ctx.tasks)
        existing = None
        for i in range(self._ctx.tasks_layout.count()):
            w = self._ctx.tasks_layout.itemAt(i).widget()
            if isinstance(w, PriorityHeaderWidget):
                existing = (i, w)
                break
        if has_high and existing is None:
            theme_id = normalize_theme_id(self._ctx.app_state.get("theme", "dark"))
            header = PriorityHeaderWidget(theme_id=theme_id)
            self._ctx.tasks_layout.insertWidget(0, header, 0, Qt.AlignmentFlag.AlignTop)
        elif not has_high and existing is not None:
            idx, header = existing
            self._ctx.tasks_layout.removeWidget(header)
            header.deleteLater()

    def _show_task_context_menu_at(self, task_ref: dict, global_pos: QPoint) -> None:
        """Show the task context menu. This is called from TaskRowWidget callbacks."""
        if self._ctx.on_show_context_menu:
            self._ctx.on_show_context_menu(task_ref)

    # ------------------------------------------------------------------
    # Task editing
    # ------------------------------------------------------------------

    def edit_task(self, task_ref: dict) -> None:
        row = self._ctx.task_row_widgets.get(id(task_ref))
        if row is not None:
            row.begin_edit()

    def update_task_text(self, task_ref: dict, new_text: str) -> None:
        task_ref["text"] = new_text
        self._ctx.store.save(self._ctx.tasks)

    # ------------------------------------------------------------------
    # Task deletion
    # ------------------------------------------------------------------

    def delete_task(self, task_ref: dict) -> None:
        if not ThemedMessageDialog.question(None, "Delete Task", "Are you sure you want to delete this task? This cannot be undone."):
            return
        if task_ref in self._ctx.tasks:
            self._ctx.timer_manager.cancel_task_reminder(task_ref["id"])
            self._ctx.tasks.remove(task_ref)
            self._ctx.store.save(self._ctx.tasks)
            self._remove_task_row_widget(task_ref)

    # ------------------------------------------------------------------
    # Task completion toggle / archive
    # ------------------------------------------------------------------

    def toggle_task(self, task_ref: dict, is_checked: bool) -> None:
        task_ref["done"] = is_checked
        if is_checked:
            if self._ctx.sound_manager is not None:
                self._ctx.sound_manager.play_completion()
            self.archive_task(task_ref)
            self._recalculate_section_dividers()
            return

        self._ctx.store.save(self._ctx.tasks)
        self._recalculate_section_dividers()

    def archive_task(self, task_ref: dict) -> None:
        if task_ref not in self._ctx.tasks:
            return

        self._ctx.timer_manager.cancel_task_reminder(task_ref["id"])
        original_index = self._ctx.tasks.index(task_ref)

        archived_task = dict(task_ref)
        archived_task["done"] = True
        archived_task["completedAt"] = datetime.now().isoformat()

        self._ctx.history_store.append_and_save(archived_task)

        self._ctx.tasks.remove(task_ref)

        if RecurrenceManager.should_recreate(task_ref):
            new_task = RecurrenceManager.create_next_instance(task_ref)
            if original_index < len(self._ctx.tasks):
                self._ctx.tasks.insert(original_index, new_task)
            else:
                self._ctx.tasks.append(new_task)
            self._append_task_row_widget(new_task)

        self._ctx.store.save(self._ctx.tasks)
        self._remove_task_row_widget(task_ref)
        if self._ctx.history_dialog is not None:
            try:
                self._ctx.history_dialog.add_external_archived_task(archived_task)
            except RuntimeError:
                self._ctx.history_dialog = None

        archived_task["_archivedFromIndex"] = original_index
        self._ctx.last_archived_task = archived_task
        self._show_undo_toast(task_ref.get("text", "Task"))

    # ------------------------------------------------------------------
    # Bulk clear
    # ------------------------------------------------------------------

    def clear_completed_tasks(self) -> None:
        completed = [t for t in self._ctx.tasks if t.get("done", False)]
        if not completed:
            return
        if not ThemedMessageDialog.question(None, "Clear Completed Tasks", "Are you sure you want to clear all completed tasks? They will be moved to history."):
            return

        history = self._ctx.history_store.load()
        for task in completed:
            archived_task = dict(task)
            archived_task["done"] = True
            archived_task["completedAt"] = datetime.now().isoformat()
            history.append(archived_task)
        self._ctx.history_store.save(history)

        self._ctx.tasks = [t for t in self._ctx.tasks if not t.get("done", False)]
        self._ctx.store.save(self._ctx.tasks)
        self._ctx.on_render_tasks()

    # ------------------------------------------------------------------
    # Reorder / drag-drop
    # ------------------------------------------------------------------

    def _reorder_task(self, task_ref: dict, new_idx: int) -> None:
        group_id = task_ref.get("groupId", GENERAL_GROUP_ID)
        groups_enabled = self._ctx.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)
        if groups_enabled:
            group_tasks = tasks_for_group(self._ctx.tasks, group_id, include_done=True)
            if task_ref not in group_tasks:
                return
            idx = group_tasks.index(task_ref)
            if idx == new_idx:
                return
            group_tasks.insert(new_idx, group_tasks.pop(idx))
            self._ctx.tasks = rebuild_tasks_preserving_groups(
                self._ctx.tasks, self._ctx.groups_data, group_id, group_tasks
            )
            section = self._ctx.group_sections.get(group_id)
            row = self._ctx.task_row_widgets.get(id(task_ref))
            if section is not None and row is not None:
                section.content_layout.removeWidget(row)
                if row in section.task_rows:
                    section.task_rows.remove(row)
                section.add_task_row(row, index=new_idx)
                section.refresh_header_count()
        else:
            if task_ref not in self._ctx.tasks:
                return
            idx = self._ctx.tasks.index(task_ref)
            if idx == new_idx:
                return
            self._ctx.tasks.insert(new_idx, self._ctx.tasks.pop(idx))
            row = self._ctx.task_row_widgets.get(id(task_ref))
            if row is not None:
                self._ctx.tasks_layout.removeWidget(row)
                self._ctx.tasks_layout.insertWidget(new_idx, row, 0, Qt.AlignmentFlag.AlignTop)
        self._ctx.store.save(self._ctx.tasks)
        self._ctx.on_sync_row_text_layouts()

    def move_task(self, task_ref: dict, offset: int) -> None:
        group_id = task_ref.get("groupId", GENERAL_GROUP_ID)
        groups_enabled = self._ctx.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)
        if groups_enabled:
            group_tasks = tasks_for_group(self._ctx.tasks, group_id, include_done=True)
            if task_ref not in group_tasks:
                return
            idx = group_tasks.index(task_ref)
            new_idx = idx + offset
            if 0 <= new_idx < len(group_tasks):
                self._reorder_task(task_ref, new_idx)
        else:
            if task_ref not in self._ctx.tasks:
                return
            idx = self._ctx.tasks.index(task_ref)
            new_idx = idx + offset
            if 0 <= new_idx < len(self._ctx.tasks):
                self._reorder_task(task_ref, new_idx)

    def move_task_to_top(self, task_ref: dict) -> None:
        self._reorder_task(task_ref, 0)

    def move_task_to_bottom(self, task_ref: dict) -> None:
        group_id = task_ref.get("groupId", GENERAL_GROUP_ID)
        groups_enabled = self._ctx.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)
        if groups_enabled:
            group_tasks = tasks_for_group(self._ctx.tasks, group_id, include_done=True)
            self._reorder_task(task_ref, len(group_tasks) - 1)
        else:
            self._reorder_task(task_ref, len(self._ctx.tasks) - 1)

    def _on_flat_list_drop(self, row_widget, pos: QPoint) -> None:
        task_ref = getattr(row_widget, "_task_ref", None)
        if task_ref is None or task_ref not in self._ctx.tasks:
            return
        old_idx = self._ctx.tasks.index(task_ref)
        other_widgets = []
        for i in range(self._ctx.tasks_layout.count()):
            item = self._ctx.tasks_layout.itemAt(i)
            w = item.widget() if item is not None else None
            if w is not None and w is not row_widget and hasattr(w, "_task_ref") and not w.isHidden():
                other_widgets.append(w)
        insert_idx = len(other_widgets)
        for i, w in enumerate(other_widgets):
            if pos.y() < w.y() + w.height() // 2:
                insert_idx = i
                break
        if insert_idx < 0 or insert_idx == old_idx:
            return
        self._ctx.tasks_layout.removeWidget(row_widget)
        if insert_idx < len(other_widgets):
            target = other_widgets[insert_idx]
            li = self._ctx.tasks_layout.indexOf(target)
            self._ctx.tasks_layout.insertWidget(li, row_widget, 0, Qt.AlignmentFlag.AlignTop)
        else:
            li = self._layout_stretch_index()
            if li >= 0:
                self._ctx.tasks_layout.insertWidget(li, row_widget, 0, Qt.AlignmentFlag.AlignTop)
            else:
                self._ctx.tasks_layout.addWidget(row_widget, 0, Qt.AlignmentFlag.AlignTop)
        self._ctx.tasks.pop(old_idx)
        self._ctx.tasks.insert(insert_idx, task_ref)
        self._ctx.store.save(self._ctx.tasks)
        self._ctx.on_sync_row_text_layouts()

    def _layout_stretch_index(self) -> int:
        for i in range(self._ctx.tasks_layout.count()):
            item = self._ctx.tasks_layout.itemAt(i)
            if item is not None and item.widget() is None and item.spacerItem() is not None:
                return i
        return -1

    def _update_flat_drop_indicator(self, pos: QPoint) -> None:
        visible = []
        for i in range(self._ctx.tasks_layout.count()):
            item = self._ctx.tasks_layout.itemAt(i)
            w = item.widget() if item is not None else None
            if w is not None and hasattr(w, "_task_ref") and not w.isHidden():
                visible.append(w)
        if not visible:
            self._ctx.flat_drop_indicator.hide()
            return
        insert_idx = len(visible)
        for i, w in enumerate(visible):
            if pos.y() < w.y() + w.height() // 2:
                insert_idx = i
                break
        y_pos = 0
        if insert_idx < len(visible):
            y_pos = visible[insert_idx].y() - 1
        else:
            y_pos = visible[-1].y() + visible[-1].height() - 1
        self._ctx.flat_drop_indicator.move(0, max(0, y_pos))
        self._ctx.flat_drop_indicator.setFixedWidth(self._ctx.tasks_widget.width())
        self._ctx.flat_drop_indicator.show()

    def _update_group_drop_indicator(self, pos: QPoint) -> None:
        from src.frontend.task_group_section import TaskGroupSection
        sections = []
        for i in range(self._ctx.tasks_layout.count()):
            item = self._ctx.tasks_layout.itemAt(i)
            w = item.widget() if item is not None else None
            if isinstance(w, TaskGroupSection) and not w.isHidden():
                sections.append(w)
        if not sections:
            self._ctx.group_drop_indicator.hide()
            return
        insert_idx = len(sections)
        for i, s in enumerate(sections):
            if pos.y() < s.y() + s.height() // 2:
                insert_idx = i
                break
        y_pos = 0
        if insert_idx < len(sections):
            y_pos = sections[insert_idx].y() - 1
        else:
            y_pos = sections[-1].y() + sections[-1].height() - 1
        self._ctx.group_drop_indicator.move(0, max(0, y_pos))
        self._ctx.group_drop_indicator.setFixedWidth(self._ctx.tasks_widget.width())
        self._ctx.group_drop_indicator.show()

    def _on_group_drop(self, pos: QPoint, mime_data) -> None:
        self._ctx.group_drop_indicator.hide()
        group_id_bytes = mime_data.data("application/x-nudge-group").data()
        if not group_id_bytes:
            return
        source_id = group_id_bytes.decode()
        from src.frontend.task_group_section import TaskGroupSection
        sections = []
        for i in range(self._ctx.tasks_layout.count()):
            item = self._ctx.tasks_layout.itemAt(i)
            w = item.widget() if item is not None else None
            if isinstance(w, TaskGroupSection) and not w.isHidden():
                sections.append(w)
        target_idx = len(sections)
        for i, s in enumerate(sections):
            if pos.y() < s.y() + s.height() // 2:
                target_idx = i
                break
        groups = self._ctx.groups_data.get("groups", [])
        src_idx = next((i for i, g in enumerate(groups) if g["id"] == source_id), -1)
        if src_idx < 0:
            return
        if src_idx == target_idx or (src_idx < target_idx and target_idx - 1 == src_idx):
            return
        group = groups.pop(src_idx)
        if target_idx > src_idx:
            target_idx -= 1
        groups.insert(target_idx, group)
        for i, g in enumerate(groups):
            g["order"] = i
        self._ctx.group_store.save(self._ctx.groups_data)
        self.render_tasks(force=True)

    def _on_row_dropped(self, row_widget, target_group_id: str, insert_index: int) -> None:
        task_ref = getattr(row_widget, "_task_ref", None)
        if task_ref is None:
            return
        old_group_id = task_ref.get("groupId", GENERAL_GROUP_ID)
        if old_group_id == target_group_id:
            group_tasks = tasks_for_group(self._ctx.tasks, old_group_id, include_done=True)
            if task_ref not in group_tasks:
                return
            idx = group_tasks.index(task_ref)
            if idx == insert_index or insert_index < 0:
                return
            if insert_index > idx:
                insert_index -= 1
            group_tasks.insert(insert_index, group_tasks.pop(idx))
            self._ctx.tasks = rebuild_tasks_preserving_groups(
                self._ctx.tasks, self._ctx.groups_data, old_group_id, group_tasks
            )
            self._ctx.store.save(self._ctx.tasks)
            section = self._ctx.group_sections.get(old_group_id)
            if section is not None:
                section.content_layout.removeWidget(row_widget)
                if row_widget in section.task_rows:
                    section.task_rows.remove(row_widget)
                section.add_task_row(row_widget, index=insert_index)
                section.refresh_header_count()
        else:
            old_section = self._ctx.group_sections.get(old_group_id)
            if old_section is not None:
                old_section.content_layout.removeWidget(row_widget)
                if row_widget in old_section.task_rows:
                    old_section.task_rows.remove(row_widget)
                old_section.refresh_header_count()
            task_ref["groupId"] = target_group_id
            self._ctx.store.save(self._ctx.tasks)
            new_section = self._ctx.group_sections.get(target_group_id)
            if new_section is not None:
                new_section.add_task_row(row_widget, index=insert_index)
                new_section.refresh_header_count()
        self._ctx.on_sync_row_text_layouts()
        self._recalculate_section_dividers()

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def _show_undo_toast(self, task_text: str) -> None:
        if self._ctx.active_undo_toast is not None:
            self._ctx.active_undo_toast._dismiss()
            self._ctx.active_undo_toast = None

        def on_dismissed():
            self._ctx.active_undo_toast = None

        from PyQt6.QtCore import Qt as _Qt
        toast = UndoToast(
            self._ctx.main_window,
            "Task completed",
            self._undo_last_archive,
            dismissed_callback=on_dismissed,
            detail=task_text,
        )
        toast.setWindowFlags(
            _Qt.WindowType.FramelessWindowHint |
            _Qt.WindowType.Tool | _Qt.WindowType.WindowStaysOnTopHint
        )
        toast._apply_theme()
        toast._reposition()
        toast.show()
        toast.raise_()
        self._ctx.active_undo_toast = toast

    def _undo_last_archive(self) -> None:
        task = self._ctx.last_archived_task
        if task is None:
            return
        self._ctx.last_archived_task = None
        self.restore_task_from_history(task)

    def restore_task_from_history(self, task_ref: dict) -> None:
        original_index = task_ref.pop("_archivedFromIndex", None)

        history = self._ctx.history_store.load()
        if task_ref in history:
            history.remove(task_ref)
            self._ctx.history_store.save(history)

        restored_task = dict(task_ref)
        restored_task["done"] = False
        restored_task.pop("completedAt", None)
        for key in ("reminderAt", "reminderFired", "reminderRepeat"):
            restored_task.pop(key, None)

        if original_index is not None and 0 <= original_index <= len(self._ctx.tasks):
            self._ctx.tasks.insert(original_index, restored_task)
        else:
            self._ctx.tasks.append(restored_task)

        self._ctx.store.save(self._ctx.tasks)
        self._ctx.on_render_tasks()

    # ------------------------------------------------------------------
    # Migration
    # ------------------------------------------------------------------

    def migrate_completed_tasks_to_history(self) -> None:
        completed = [task for task in self._ctx.tasks if task.get("done", False)]
        if not completed:
            return

        history = self._ctx.history_store.load()
        for task in completed:
            archived_task = dict(task)
            archived_task["done"] = True
            archived_task.setdefault("completedAt", datetime.now().isoformat())
            history.append(archived_task)

        self._ctx.history_store.save(history)
        self._ctx.tasks = [task for task in self._ctx.tasks if not task.get("done", False)]
        self._ctx.store.save(self._ctx.tasks)

    # ------------------------------------------------------------------
    # Reminder CRUD
    # ------------------------------------------------------------------

    def _set_task_reminder(self, task_ref: dict, minutes_from_now: int, repeat: int = 0) -> None:
        trigger_at = datetime.now() + timedelta(minutes=minutes_from_now)
        self._ctx.timer_manager.cancel_task_reminder(task_ref["id"])
        self._ctx.timer_manager.add_task_reminder(
            task_id=task_ref["id"],
            name=task_ref.get("text", "Task reminder"),
            trigger_at=trigger_at,
            repeat_minutes=repeat,
        )
        self._ctx.app_state["timers"] = self._ctx.timer_manager.to_list()
        self._ctx.state_manager.save()
        row = self._ctx.task_row_widgets.get(id(task_ref))
        if row is not None:
            row.set_task_ref(task_ref)

    def _set_task_reminder_at_time(self, task_ref: dict, time_str: str, days_ahead: int = 0) -> None:
        now = datetime.now()
        parts = time_str.split(":")
        target = now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0, microsecond=0)
        if days_ahead > 0:
            target += timedelta(days=days_ahead)
        if target <= now:
            target += timedelta(days=1)
        self._ctx.timer_manager.cancel_task_reminder(task_ref["id"])
        self._ctx.timer_manager.add_task_reminder(
            task_id=task_ref["id"],
            name=task_ref.get("text", "Task reminder"),
            trigger_at=target,
            repeat_minutes=0,
        )
        self._ctx.app_state["timers"] = self._ctx.timer_manager.to_list()
        self._ctx.state_manager.save()
        row = self._ctx.task_row_widgets.get(id(task_ref))
        if row is not None:
            row.set_task_ref(task_ref)

    def _clear_task_reminder(self, task_ref: dict) -> None:
        self._ctx.timer_manager.cancel_task_reminder(task_ref["id"])
        self._ctx.app_state["timers"] = self._ctx.timer_manager.to_list()
        self._ctx.state_manager.save()
        row = self._ctx.task_row_widgets.get(id(task_ref))
        if row is not None:
            row.set_task_ref(task_ref)

    # ------------------------------------------------------------------
    # Due date CRUD
    # ------------------------------------------------------------------

    def _set_task_due_date(self, task_ref: dict, date_str: str) -> None:
        task_ref["dueDate"] = date_str
        self._ctx.store.save(self._ctx.tasks)
        row = self._ctx.task_row_widgets.get(id(task_ref))
        if row:
            row.set_task_ref(task_ref)

    def _clear_task_due_date(self, task_ref: dict) -> None:
        task_ref["dueDate"] = None
        self._ctx.store.save(self._ctx.tasks)
        row = self._ctx.task_row_widgets.get(id(task_ref))
        if row:
            row.set_task_ref(task_ref)

    def _show_custom_due_date_dialog(self, task_ref: dict) -> None:
        from src.frontend.dialog_context import DialogContext
        from src.frontend.custom_due_date_dialog import CustomDueDateDialog
        ctx = DialogContext(app_state=self._ctx.app_state, state_manager=self._ctx.state_manager)
        dialog = CustomDueDateDialog(
            ctx, task_ref,
            on_accept=self._set_task_due_date,
            parent=None,
        )
        dialog.exec()

    # ------------------------------------------------------------------
    # Priority CRUD
    # ------------------------------------------------------------------

    def _set_task_priority(self, task_ref: dict, priority: str) -> None:
        task_ref["priority"] = priority
        self._ctx.store.save(self._ctx.tasks)
        groups_enabled = self._ctx.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)
        if not groups_enabled:
            self.render_tasks()
        else:
            row = self._ctx.task_row_widgets.get(id(task_ref))
            if row:
                row.set_task_ref(task_ref)
        self._recalculate_section_dividers()

    def _clear_task_priority(self, task_ref: dict) -> None:
        task_ref["priority"] = None
        self._ctx.store.save(self._ctx.tasks)
        groups_enabled = self._ctx.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)
        if not groups_enabled:
            self.render_tasks()
        else:
            row = self._ctx.task_row_widgets.get(id(task_ref))
            if row:
                row.set_task_ref(task_ref)
        self._recalculate_section_dividers()

    # ------------------------------------------------------------------
    # Recurrence CRUD
    # ------------------------------------------------------------------

    def _set_task_recurrence(self, task_ref: dict, recurrence_type: str, interval: int) -> None:
        task_ref["recurrence"] = {
            "type": recurrence_type,
            "interval": interval,
        }
        self._ctx.store.save(self._ctx.tasks)

    def _clear_task_recurrence(self, task_ref: dict) -> None:
        task_ref["recurrence"] = None
        self._ctx.store.save(self._ctx.tasks)

    def _show_custom_recurrence_dialog(self, task_ref: dict) -> None:
        from src.frontend.dialog_context import DialogContext
        from src.frontend.custom_recurrence_dialog import CustomRecurrenceDialog
        ctx = DialogContext(app_state=self._ctx.app_state, state_manager=self._ctx.state_manager)
        dialog = CustomRecurrenceDialog(
            ctx, task_ref,
            on_accept=self._set_task_recurrence,
            parent=None,
        )
        dialog.exec()

    def _show_custom_reminder_dialog(self, task_ref: dict) -> None:
        from src.frontend.dialog_context import DialogContext
        from src.frontend.custom_reminder_dialog import CustomReminderDialog
        ctx = DialogContext(
            app_state=self._ctx.app_state,
            state_manager=self._ctx.state_manager,
            timer_manager=self._ctx.timer_manager,
            screen=lambda: None,
            frame_geometry=lambda: None,
            window_rects_to_avoid=lambda: [],
            place_dialog_avoiding_rects=lambda d, r, **kw: None,
            task_row_widgets=self._ctx.task_row_widgets,
        )
        dialog = CustomReminderDialog(ctx, task_ref, parent=None)
        dialog.exec()

    # ------------------------------------------------------------------
    # Group drop indicator (used by _create_widget_context in MainWindow)
    # ------------------------------------------------------------------

    def update_group_drop_indicator(self, pos) -> None:
        self._update_group_drop_indicator(pos)

    def hide_group_drop_indicator(self) -> None:
        self._ctx.group_drop_indicator.hide()

    def on_group_drop(self, pos, mime_data) -> None:
        self._on_group_drop(pos, mime_data)

    def on_row_dropped(self, source_id: str, target_group_id: str, insert_index: int) -> None:
        # This is called from WidgetContext — find the row widget
        for task_id_key, row in self._ctx.task_row_widgets.items():
            task_ref = getattr(row, "_task_ref", None)
            if task_ref is not None and task_ref.get("id") == source_id:
                self._on_row_dropped(row, target_group_id, insert_index)
                return
