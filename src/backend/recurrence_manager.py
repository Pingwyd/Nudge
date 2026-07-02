"""RecurrenceManager handles recurring task recreation on completion."""

from datetime import datetime, timedelta
from typing import Optional
import uuid


def _add_months(start: datetime, months: int) -> datetime:
    """Add months to a date, clamping to end-of-month."""
    month = start.month - 1 + months
    year = start.year + month // 12
    month = month % 12 + 1
    import calendar
    max_day = calendar.monthrange(year, month)[1]
    day = min(start.day, max_day)
    return start.replace(year=year, month=month, day=day)


class RecurrenceManager:
    """Manages recurring tasks - calculates next due dates and creates task copies."""

    @staticmethod
    def calculate_next_due(current_due: str, recurrence: dict) -> str:
        """
        Calculate the next due date based on recurrence settings.
        Skips forward to the next future date if the natural next falls in the past.
        """
        if not current_due or not recurrence:
            return current_due

        current_date = datetime.strptime(current_due, "%Y-%m-%d").date()
        recurrence_type = recurrence.get("type", "daily")
        interval = recurrence.get("interval", 1)

        next_date = current_date
        if recurrence_type == "daily":
            next_date = current_date + timedelta(days=interval)
        elif recurrence_type == "weekly":
            next_date = current_date + timedelta(weeks=interval)
        elif recurrence_type == "monthly":
            next_date = _add_months(datetime.combine(current_date, datetime.min.time()), interval).date()
        elif recurrence_type == "yearly":
            next_date = _add_months(datetime.combine(current_date, datetime.min.time()), interval * 12).date()
        else:
            return current_due

        today = datetime.now().date()
        if next_date <= today:
            if recurrence_type == "daily":
                days_past = (today - current_date).days
                skips = (days_past // interval) + 1
                next_date = current_date + timedelta(days=skips * interval)
            elif recurrence_type == "weekly":
                weeks_past = (today - current_date).days // 7
                skips = (weeks_past // interval) + 1
                next_date = current_date + timedelta(weeks=skips * interval)
            elif recurrence_type in ("monthly", "yearly"):
                # Recalculate from anchor, stepping forward until future
                factor = 12 if recurrence_type == "yearly" else 1
                step = interval * factor
                n = 1
                while True:
                    cand = _add_months(datetime.combine(current_date, datetime.min.time()), step * n).date()
                    if cand > today:
                        next_date = cand
                        break
                    n += 1

        return next_date.strftime("%Y-%m-%d")

    @staticmethod
    def should_recreate(task: dict) -> bool:
        """Check if a task should be recreated after completion."""
        recurrence = task.get("recurrence")
        if not recurrence:
            return False
        valid_types = {"daily", "weekly", "monthly", "yearly"}
        return (
            recurrence.get("type") in valid_types
            and task.get("dueDate") is not None
        )

    @staticmethod
    def create_next_instance(task: dict) -> dict:
        """Create a new task instance for the next occurrence."""
        if not RecurrenceManager.should_recreate(task):
            return task

        current_due = task.get("dueDate")
        recurrence = task.get("recurrence")
        next_due = RecurrenceManager.calculate_next_due(current_due, recurrence)

        return {
            "id": str(uuid.uuid4()),
            "text": task.get("text", ""),
            "done": False,
            "createdAt": datetime.now().isoformat(),
            "order": task.get("order", 0),
            "dueDate": next_due,
            "priority": task.get("priority"),
            "tags": task.get("tags", []).copy(),
            "recurrence": task.get("recurrence"),
        }

    @staticmethod
    def get_recurrence_display(recurrence: dict) -> str:
        """Human-readable display like 'Daily', 'Weekly', 'Every 2 Weeks'."""
        if not recurrence:
            return ""
        rtype = recurrence.get("type", "daily")
        interval = recurrence.get("interval", 1)
        if interval == 1:
            return rtype.capitalize()
        # Proper pluralization: weekly -> weeks, daily -> days, monthly -> months
        plural_map = {"daily": "days", "weekly": "weeks", "monthly": "months", "yearly": "years"}
        plural = plural_map.get(rtype, f"{rtype}s")
        return f"Every {interval} {plural}"
