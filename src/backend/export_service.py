"""
Export tasks (and optional history) to .txt, .md, or .csv with group sections (Stage 10).
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Literal, Tuple

from src.backend.task_groups import (
    GENERAL_GROUP_ID,
    group_name,
    sorted_groups,
    tasks_for_group,
)

ExportFormat = Literal["txt", "md", "csv"]


@dataclass
class ExportRequest:
    filepath: Path
    export_format: ExportFormat
    include_history: bool
    active_tasks: List[dict]
    history_tasks: List[dict]
    groups_doc: dict


def _format_date(iso_value: str | None) -> str:
    if not iso_value:
        return ""
    return iso_value.split("T")[0]


def _task_status(task: dict, from_history: bool = False) -> str:
    if from_history:
        return "completed"
    return "completed" if task.get("done") else "active"


def _iter_active_by_group(tasks: List[dict], groups_doc: dict) -> Iterable[Tuple[str, str, List[dict]]]:
    for group in sorted_groups(groups_doc):
        gid = group["id"]
        group_tasks = tasks_for_group(tasks, gid, include_done=False)
        yield gid, group.get("name", group_name(groups_doc, gid)), group_tasks


def _iter_history_by_group(history: List[dict], groups_doc: dict) -> Iterable[Tuple[str, str, List[dict]]]:
    for group in sorted_groups(groups_doc):
        gid = group["id"]
        items = [t for t in history if t.get("groupId", GENERAL_GROUP_ID) == gid]
        yield gid, group.get("name", group_name(groups_doc, gid)), items


def _has_any_content(request: ExportRequest) -> bool:
    if any(tasks for _, _, tasks in _iter_active_by_group(request.active_tasks, request.groups_doc)):
        return True
    if request.include_history:
        return any(items for _, _, items in _iter_history_by_group(request.history_tasks, request.groups_doc))
    return False


def export_to_file(request: ExportRequest) -> None:
    """Write export content to disk using UTF-8 encoding."""
    builders = {
        "txt": _build_txt,
        "md": _build_md,
        "csv": _build_csv,
    }
    builder = builders[request.export_format]
    content = builder(request)
    request.filepath.parent.mkdir(parents=True, exist_ok=True)
    request.filepath.write_text(content, encoding="utf-8")


def _build_txt(request: ExportRequest) -> str:
    lines: List[str] = []
    lines.append("Nudge Export")
    lines.append("")

    has_active = False
    for _, name, group_tasks in _iter_active_by_group(request.active_tasks, request.groups_doc):
        lines.append(f"=== {name} ===")
        if group_tasks:
            has_active = True
            for task in group_tasks:
                lines.append(task.get("text", ""))
        else:
            lines.append("(no tasks)")
        lines.append("")

    if request.include_history:
        lines.append("=== History ===")
        has_history = False
        for _, name, items in _iter_history_by_group(request.history_tasks, request.groups_doc):
            lines.append(f"--- {name} ---")
            if items:
                has_history = True
                for task in items:
                    date_str = _format_date(task.get("completedAt") or task.get("createdAt"))
                    lines.append(f"[{date_str}] {task.get('text', '')}")
            else:
                lines.append("(no entries)")
            lines.append("")

    if not has_active and not (request.include_history and any(
        items for _, _, items in _iter_history_by_group(request.history_tasks, request.groups_doc)
    )):
        lines.append("(No tasks to export)")

    return "\n".join(lines).rstrip() + "\n"


def _build_md(request: ExportRequest) -> str:
    lines: List[str] = ["# Nudge Export", ""]

    for _, name, group_tasks in _iter_active_by_group(request.active_tasks, request.groups_doc):
        lines.append(f"## {name}")
        if group_tasks:
            for task in group_tasks:
                lines.append(f"- {task.get('text', '')}")
        else:
            lines.append("- *(no tasks)*")
        lines.append("")

    if request.include_history:
        lines.append("## History")
        lines.append("")
        for _, name, items in _iter_history_by_group(request.history_tasks, request.groups_doc):
            lines.append(f"### {name}")
            if items:
                for task in items:
                    date_str = _format_date(task.get("completedAt") or task.get("createdAt"))
                    lines.append(f"- [{date_str}] {task.get('text', '')}")
            else:
                lines.append("- *(no entries)*")
            lines.append("")

    if not _has_any_content(request):
        lines.append("*(No tasks to export)*")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_csv(request: ExportRequest) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    writer.writerow(["section", "group", "task_text", "date", "status"])

    for _, name, group_tasks in _iter_active_by_group(request.active_tasks, request.groups_doc):
        for task in group_tasks:
            writer.writerow(
                [
                    "active",
                    name,
                    task.get("text", ""),
                    _format_date(task.get("createdAt")),
                    _task_status(task),
                ]
            )

    if request.include_history:
        for _, name, items in _iter_history_by_group(request.history_tasks, request.groups_doc):
            for task in items:
                writer.writerow(
                    [
                        "history",
                        name,
                        task.get("text", ""),
                        _format_date(task.get("completedAt") or task.get("createdAt")),
                        _task_status(task, from_history=True),
                    ]
                )

    return buffer.getvalue()


def file_filter_for_format(export_format: ExportFormat) -> Tuple[str, str]:
    filters = {
        "txt": ("Plain Text (*.txt)", ".txt"),
        "md": ("Markdown (*.md)", ".md"),
        "csv": ("CSV (*.csv)", ".csv"),
    }
    return filters[export_format]
