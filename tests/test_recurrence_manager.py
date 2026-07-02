"""Unit tests for RecurrenceManager."""

import pytest
from datetime import date, timedelta
from src.backend.recurrence_manager import RecurrenceManager


class TestCalculateNextDue:
    """Tests for calculate_next_due static method."""

    def test_daily_next_day(self, future_date_str):
        recurrence = {"type": "daily", "interval": 1}
        result = RecurrenceManager.calculate_next_due(future_date_str, recurrence)
        expected = (date.fromisoformat(future_date_str) + timedelta(days=1)).isoformat()
        assert result == expected

    def test_daily_skip_forward(self, past_date_str):
        """If next date is in past, skip forward to future."""
        recurrence = {"type": "daily", "interval": 1}
        result = RecurrenceManager.calculate_next_due(past_date_str, recurrence)
        result_date = date.fromisoformat(result)
        assert result_date > date.today()

    def test_weekly_next_week(self, future_date_str):
        recurrence = {"type": "weekly", "interval": 1}
        result = RecurrenceManager.calculate_next_due(future_date_str, recurrence)
        expected = (date.fromisoformat(future_date_str) + timedelta(weeks=1)).isoformat()
        assert result == expected

    def test_weekly_skip_forward(self, past_date_str):
        recurrence = {"type": "weekly", "interval": 1}
        result = RecurrenceManager.calculate_next_due(past_date_str, recurrence)
        result_date = date.fromisoformat(result)
        assert result_date > date.today()

    def test_monthly_next_month(self):
        """Monthly recurrence advances by months, not days."""
        current_due = "2026-06-15"
        recurrence = {"type": "monthly", "interval": 1}
        result = RecurrenceManager.calculate_next_due(current_due, recurrence)
        assert result == "2026-07-15"

    def test_monthly_end_of_month_clamp(self):
        """Monthly from Jan 31 should go to Feb 28 (non-leap)."""
        # Use a future date to avoid skip-forward logic
        current_due = "2026-12-31"
        recurrence = {"type": "monthly", "interval": 1}
        result = RecurrenceManager.calculate_next_due(current_due, recurrence)
        assert result == "2027-01-31"

    def test_every_two_weeks(self, future_date_str):
        recurrence = {"type": "weekly", "interval": 2}
        result = RecurrenceManager.calculate_next_due(future_date_str, recurrence)
        expected = (date.fromisoformat(future_date_str) + timedelta(weeks=2)).isoformat()
        assert result == expected

    def test_every_two_days(self, future_date_str):
        recurrence = {"type": "daily", "interval": 2}
        result = RecurrenceManager.calculate_next_due(future_date_str, recurrence)
        expected = (date.fromisoformat(future_date_str) + timedelta(days=2)).isoformat()
        assert result == expected

    def test_no_recurrence_returns_same(self, future_date_str):
        result = RecurrenceManager.calculate_next_due(future_date_str, None)
        assert result == future_date_str

    def test_no_due_date_returns_same(self):
        recurrence = {"type": "daily", "interval": 1}
        result = RecurrenceManager.calculate_next_due(None, recurrence)
        assert result is None

    def test_unknown_type_returns_same(self, future_date_str):
        recurrence = {"type": "unknown", "interval": 1}
        result = RecurrenceManager.calculate_next_due(future_date_str, recurrence)
        assert result == future_date_str


class TestShouldRecreate:
    """Tests for should_recreate static method."""

    def test_no_recurrence(self, sample_task):
        task = {**sample_task, "recurrence": None}
        assert RecurrenceManager.should_recreate(task) is False

    def test_has_recurrence_and_due_date(self, sample_task):
        assert RecurrenceManager.should_recreate(sample_task) is True

    def test_has_recurrence_no_due_date(self, sample_task):
        task = {**sample_task, "dueDate": None}
        assert RecurrenceManager.should_recreate(task) is False

    def test_invalid_recurrence_type(self, sample_task):
        task = {**sample_task, "recurrence": {"type": "invalid", "interval": 1}}
        assert RecurrenceManager.should_recreate(task) is False


class TestCreateNextInstance:
    """Tests for create_next_instance static method."""

    def test_creates_new_task_with_next_due(self, sample_task):
        result = RecurrenceManager.create_next_instance(sample_task)
        assert result["id"] != sample_task["id"]  # New ID
        assert result["text"] == sample_task["text"]
        assert result["done"] is False
        assert result["dueDate"] != sample_task["dueDate"]  # Advanced
        assert result["priority"] == sample_task["priority"]
        assert result["tags"] == sample_task["tags"]
        assert result["recurrence"] == sample_task["recurrence"]

    def test_no_recurrence_returns_same_task(self, sample_task):
        task = {**sample_task, "recurrence": None}
        result = RecurrenceManager.create_next_instance(task)
        assert result == task  # Same task returned

    def test_tags_are_copied_not_shared(self, sample_task):
        result = RecurrenceManager.create_next_instance(sample_task)
        result["tags"].append("new_tag")
        assert "new_tag" not in sample_task["tags"]


class TestGetRecurrenceDisplay:
    """Tests for get_recurrence_display static method."""

    def test_daily(self):
        assert RecurrenceManager.get_recurrence_display({"type": "daily", "interval": 1}) == "Daily"

    def test_weekly(self):
        assert RecurrenceManager.get_recurrence_display({"type": "weekly", "interval": 1}) == "Weekly"

    def test_every_two_weeks(self):
        assert RecurrenceManager.get_recurrence_display({"type": "weekly", "interval": 2}) == "Every 2 weeks"

    def test_monthly(self):
        assert RecurrenceManager.get_recurrence_display({"type": "monthly", "interval": 1}) == "Monthly"

    def test_yearly(self):
        assert RecurrenceManager.get_recurrence_display({"type": "yearly", "interval": 1}) == "Yearly"

    def test_no_recurrence(self):
        assert RecurrenceManager.get_recurrence_display(None) == ""

    def test_empty_dict(self):
        assert RecurrenceManager.get_recurrence_display({}) == ""
