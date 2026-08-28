"""Shared test fixtures for Nudge backend tests."""

import sys
import pytest
from datetime import datetime, date, timedelta


@pytest.fixture
def sample_task():
    """A sample task with all fields populated."""
    return {
        "id": "test-123",
        "text": "Buy groceries",
        "done": False,
        "createdAt": datetime.now().isoformat(),
        "order": 0,
        "dueDate": "2026-07-15",
        "priority": "high",
        "tags": ["errands", "shopping"],
        "recurrence": {"type": "weekly", "interval": 1},
    }


@pytest.fixture
def sample_tasks():
    """A list of 5 tasks with varied properties."""
    return [
        {
            "id": "task-1",
            "text": "High priority task",
            "done": False,
            "createdAt": datetime.now().isoformat(),
            "order": 0,
            "dueDate": "2026-07-01",
            "priority": "high",
            "tags": ["urgent"],
            "recurrence": None,
        },
        {
            "id": "task-2",
            "text": "Normal task with due date",
            "done": False,
            "createdAt": datetime.now().isoformat(),
            "order": 1,
            "dueDate": "2026-07-10",
            "priority": None,
            "tags": ["work"],
            "recurrence": {"type": "daily", "interval": 1},
        },
        {
            "id": "task-3",
            "text": "Completed task",
            "done": True,
            "createdAt": datetime.now().isoformat(),
            "order": 2,
            "dueDate": None,
            "priority": None,
            "tags": [],
            "recurrence": None,
        },
        {
            "id": "task-4",
            "text": "Task with multiple tags",
            "done": False,
            "createdAt": datetime.now().isoformat(),
            "order": 3,
            "dueDate": "2026-06-25",
            "priority": "high",
            "tags": ["project", "backend", "urgent"],
            "recurrence": {"type": "monthly", "interval": 1},
        },
        {
            "id": "task-5",
            "text": "Simple task",
            "done": False,
            "createdAt": datetime.now().isoformat(),
            "order": 4,
            "dueDate": None,
            "priority": None,
            "tags": [],
            "recurrence": None,
        },
    ]


@pytest.fixture
def today_str():
    """Today's date as ISO string."""
    return date.today().isoformat()


@pytest.fixture
def future_date_str():
    """A date 7 days from now as ISO string."""
    return (date.today() + timedelta(days=7)).isoformat()


@pytest.fixture
def past_date_str():
    """A date 7 days ago as ISO string."""
    return (date.today() - timedelta(days=7)).isoformat()
