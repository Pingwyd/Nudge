from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QComboBox, QDialog, QMenu

from src.backend.task_groups import (GENERAL_GROUP_ID, create_group,
                                     group_by_id, sorted_groups,
                                     tasks_for_group)
from src.frontend.themed_input_dialog import ThemedInputDialog
from src.frontend.themed_message_dialog import ThemedMessageDialog

if TYPE_CHECKING:
    from src.frontend.task_group_section import TaskGroupSection

logger = logging.getLogger(__name__)


@dataclass
class GroupContext:
    """Bundles the attributes GroupController needs from MainWindow."""
    groups_data: dict
    group_store: Any
    store: Any
    tasks: list[dict]
    group_combo: QComboBox
    group_sections: dict
    task_row_widgets: dict
    on_render_tasks: Callable[[], None]
    on_refresh_group_combo: Callable[..., None]
    on_sync_task_row_text_layouts: Callable[[], None]
    on_style_context_menu: Callable[[QMenu], None]
    app_state: dict


class GroupController:
    """Encapsulates group CRUD and combo management."""

    def __init__(self, ctx: GroupContext) -> None:
        self._ctx = ctx

    # ── combo helpers ────────────────────────────────────────────────────

    def _current_input_group_id(self) -> str:
        group_id = self._ctx.group_combo.currentData()
        return group_id if group_id else GENERAL_GROUP_ID

    def _refresh_group_combo(self, select_group_id: str | None = None) -> None:
        if not hasattr(self._ctx, "group_combo"):
            return
        target = select_group_id or self._current_input_group_id()
        self._ctx.group_combo.blockSignals(True)
        self._ctx.group_combo.clear()
        for group in sorted_groups(self._ctx.groups_data):
            self._ctx.group_combo.addItem(group["name"], group["id"])
        index = self._ctx.group_combo.findData(target)
        if index >= 0:
            self._ctx.group_combo.setCurrentIndex(index)
        self._ctx.group_combo.blockSignals(False)

    def _select_active_group(self, group_id: str) -> None:
        if not hasattr(self._ctx, "group_combo"):
            return
        idx = self._ctx.group_combo.findData(group_id)
        if idx < 0:
            return
        if self._ctx.group_combo.currentIndex() != idx:
            self._ctx.group_combo.setCurrentIndex(idx)

    def _save_group_expanded(self, group_id: str, expanded: bool) -> None:
        group = group_by_id(self._ctx.groups_data, group_id)
        if group is None:
            return
        group["expanded"] = expanded
        self._ctx.group_store.save(self._ctx.groups_data)

    # ── CRUD ─────────────────────────────────────────────────────────────

    def _add_group_dialog(self) -> None:
        dlg = ThemedInputDialog(None, title="New Task Group", label="Group name:")
        if not dlg.exec() == QDialog.DialogCode.Accepted:
            return
        name = dlg.get_text().strip()
        if not name:
            return
        order = len(self._ctx.groups_data.get("groups", []))
        new_group = create_group(name, order)
        self._ctx.groups_data["groups"].append(new_group)
        self._ctx.group_store.save(self._ctx.groups_data)
        self._refresh_group_combo(new_group["id"])
        self._ctx.on_render_tasks()

    def _rename_group(self, group_id: str) -> None:
        group = group_by_id(self._ctx.groups_data, group_id)
        if group is None:
            return
        dlg = ThemedInputDialog(None, title="Rename Group", label="Group name:", default_text=group["name"])
        if not dlg.exec() == QDialog.DialogCode.Accepted:
            return
        name = dlg.get_text().strip()
        if not name:
            return
        group["name"] = name
        self._ctx.group_store.save(self._ctx.groups_data)
        self._refresh_group_combo(group_id)
        section = self._ctx.group_sections.get(group_id)
        if section is not None:
            section.refresh_header_count()

    def _delete_group(self, group_id: str) -> None:
        if group_id == GENERAL_GROUP_ID:
            ThemedMessageDialog.information(None, "Cannot Delete", "The General group cannot be deleted.")
            return
        group = group_by_id(self._ctx.groups_data, group_id)
        if group is None:
            return
        count = len(tasks_for_group(self._ctx.tasks, group_id))
        message = f"Delete group \"{group['name']}\"?"
        if count:
            message += f"\n{count} task(s) will move to General."
        if not ThemedMessageDialog.question(None, "Delete Group", message, default_yes=False):
            return
        for task in self._ctx.tasks:
            if task.get("groupId") == group_id:
                task["groupId"] = GENERAL_GROUP_ID
        self._ctx.groups_data["groups"] = [
            g for g in self._ctx.groups_data["groups"] if g.get("id") != group_id
        ]
        self._ctx.group_store.save(self._ctx.groups_data)
        self._ctx.store.save(self._ctx.tasks)
        self._refresh_group_combo(GENERAL_GROUP_ID)
        self._ctx.on_render_tasks()

    def _move_group_order(self, group_id: str, offset: int) -> None:
        groups = sorted_groups(self._ctx.groups_data)
        ids = [g["id"] for g in groups]
        if group_id not in ids:
            return
        index = ids.index(group_id)
        new_index = index + offset
        if new_index < 0 or new_index >= len(groups):
            return
        groups[index], groups[new_index] = groups[new_index], groups[index]
        for order, group in enumerate(groups):
            group["order"] = order
        self._ctx.groups_data["groups"] = groups
        self._ctx.group_store.save(self._ctx.groups_data)
        self._ctx.on_render_tasks()

    # ── context menu / move ──────────────────────────────────────────────

    def _show_group_header_menu(self, group_id: str, global_pos) -> None:
        menu = QMenu(None)
        self._ctx.on_style_context_menu(menu)
        rename_action = QAction("Rename Group", None)
        rename_action.triggered.connect(lambda: self._rename_group(group_id))
        menu.addAction(rename_action)

        move_up = QAction("Move Group Up", None)
        move_up.triggered.connect(lambda: self._move_group_order(group_id, -1))
        menu.addAction(move_up)

        move_down = QAction("Move Group Down", None)
        move_down.triggered.connect(lambda: self._move_group_order(group_id, 1))
        menu.addAction(move_down)

        if group_id != GENERAL_GROUP_ID:
            menu.addSeparator()
            delete_action = QAction("Delete Group", None)
            delete_action.triggered.connect(lambda: self._delete_group(group_id))
            menu.addAction(delete_action)

        menu.exec(global_pos)

    def _move_task_to_group(self, task_ref: dict, target_group_id: str) -> None:
        old_group_id = task_ref.get("groupId", GENERAL_GROUP_ID)
        row = None
        for tid, rw in self._ctx.task_row_widgets.items():
            if rw._task_ref is task_ref:
                row = rw
                break
        old_section = self._ctx.group_sections.get(old_group_id)
        if old_section is not None and row is not None:
            old_section.content_layout.removeWidget(row)
            if row in old_section.task_rows:
                old_section.task_rows.remove(row)
            old_section.refresh_header_count()
        task_ref["groupId"] = target_group_id
        self._ctx.store.save(self._ctx.tasks)
        new_section = self._ctx.group_sections.get(target_group_id)
        if new_section is not None and row is not None:
            new_section.add_task_row(row)
            new_section.refresh_header_count()
        self._ctx.on_sync_task_row_text_layouts()

    def _tasks_in_group(self, group_id: str) -> list:
        return tasks_for_group(self._ctx.tasks, group_id, include_done=True)
