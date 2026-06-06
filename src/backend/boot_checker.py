import sys
from winotify import Notification, audio
from datetime import datetime
from typing import List
import os

class BootChecker:
    @staticmethod
    def check_and_notify(tasks: List[dict]):
        """
        Checks for any incomplete tasks that were created before today.
        If found, triggers a Windows Toast Notification.
        """
        if not tasks:
            return
            
        today_str = datetime.now().date().isoformat()
        
        pending_older_tasks = []
        for task in tasks:
            if not task.get("done", False):
                # Using simple string comparison for dates if possible, or robust parsing
                created_at_str = task.get("createdAt", "")
                if created_at_str:
                    try:
                        # Extract the date part YYYY-MM-DD
                        created_date = created_at_str.split("T")[0]
                        if created_date < today_str:
                            pending_older_tasks.append(task)
                    except Exception:
                        pass
        
        if pending_older_tasks:
            count = len(pending_older_tasks)

            icon_path = ""
            if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                icon_path = os.path.join(sys._MEIPASS, "icon.ico")
            else:
                icon_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "icon.ico",
                )
            if not os.path.exists(icon_path):
                icon_path = ""

            toast = Notification(
                app_id="Nudge",
                title="Nudge: pending tasks",
                msg=f"You have {count} incomplete task(s) from previous days. Stay focused!",
                icon=icon_path,
                duration="long"
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
