"""
Task group model helpers (Stage 6).

Groups are stored in groups.json; each task carries a groupId field.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

GENERAL_GROUP_ID = "general"
GENERAL_GROUP_NAME = "General"


def default_groups_document() -> dict:
    return {
        "groups": [
            {
                "id": GENERAL_GROUP_ID,
                "name": GENERAL_GROUP_NAME,
                "order": 0,
                "expanded": True,
            }
        ]
    }


def ensure_general_group(groups_doc: dict) -> dict:
    groups = groups_doc.setdefault("groups", [])
    if not any(g.get("id") == GENERAL_GROUP_ID for g in groups):
        groups.insert(0, default_groups_document()["groups"][0])
    return groups_doc


def sorted_groups(groups_doc: dict) -> List[dict]:
    ensure_general_group(groups_doc)
    return sorted(groups_doc["groups"], key=lambda g: (g.get("order", 0), g.get("name", "")))


def group_by_id(groups_doc: dict, group_id: str) -> Optional[dict]:
    for group in groups_doc.get("groups", []):
        if group.get("id") == group_id:
            return group
    return None


def group_name(groups_doc: dict, group_id: Optional[str]) -> str:
    group = group_by_id(groups_doc, group_id or GENERAL_GROUP_ID)
    return group["name"] if group else GENERAL_GROUP_NAME


def migrate_tasks_group_ids(tasks: List[dict]) -> List[dict]:
    """Assign General to legacy tasks missing groupId."""
    for task in tasks:
        if not task.get("groupId"):
            task["groupId"] = GENERAL_GROUP_ID
    return tasks


def create_group(name: str, order: int) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "name": name.strip(),
        "order": order,
        "expanded": True,
    }


def tasks_for_group(tasks: List[dict], group_id: str, include_done: bool = False) -> List[dict]:
    result = []
    for task in tasks:
        if task.get("groupId", GENERAL_GROUP_ID) != group_id:
            continue
        if not include_done and task.get("done", False):
            continue
        result.append(task)
    return result


def rebuild_tasks_preserving_groups(
    all_tasks: List[dict],
    groups_doc: dict,
    group_id: str,
    ordered_group_tasks: List[dict],
) -> List[dict]:
    """Replace one group's tasks in the flat list while keeping other groups' order."""
    rebuilt: List[dict] = []
    for group in sorted_groups(groups_doc):
        gid = group["id"]
        if gid == group_id:
            rebuilt.extend(ordered_group_tasks)
        else:
            rebuilt.extend(tasks_for_group(all_tasks, gid, include_done=True))
    return rebuilt
