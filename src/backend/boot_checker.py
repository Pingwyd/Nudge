import logging
import sys
from datetime import datetime
from typing import List

try:
    if sys.platform == "win32":
        from winotify import Notification, audio
    else:
        raise ImportError("winotify is Windows-only")
except ImportError:
    Notification = None
    audio = None


class BootChecker:
    @staticmethod
    def check_and_notify(tasks: List[dict]):
        """
        Checks for any incomplete tasks that were created before today.
        On Windows, shows a native toast notification.
        On other platforms or when winotify is unavailable, logs the reminder.
        """
        if not tasks:
            return

        today_str = datetime.now().date().isoformat()

        pending_older_tasks = []
        for task in tasks:
            if not task.get("done", False):
                created_at_str = task.get("createdAt", "")
                if created_at_str:
                    try:
                        created_date = created_at_str.split("T")[0]
                        if created_date < today_str:
                            pending_older_tasks.append(task)
                    except Exception as e:
                        logging.warning("Boot check failed: %s", e)

        if not pending_older_tasks:
            return

        count = len(pending_older_tasks)
        msg = f"You have {count} incomplete task(s) from previous days. Stay focused!"

        if Notification is not None and sys.platform == "win32":
            from src.backend.icon import get_app_icon_path

            icon_path = ""
            resolved = get_app_icon_path()
            if resolved is not None:
                icon_path = str(resolved)

            toast = Notification(
                app_id="Nudge",
                title="Nudge: pending tasks",
                msg=msg,
                icon=icon_path,
                duration="long",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        else:
            logging.info("Boot reminder: %s", msg)
