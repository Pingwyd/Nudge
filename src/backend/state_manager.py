import json
import os
import winreg
import sys
from pathlib import Path
from typing import Tuple

from src.backend.window_geometry import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
)
from src.backend.paths import get_data_file, migrate_legacy_data


def get_base_dir() -> Path:
    """Backwards-compatible alias — prefer :func:`src.backend.paths.get_data_dir`."""
    from src.backend.paths import get_data_dir
    return get_data_dir()


class StateManager:
    def __init__(self, filename="appstate.json"):
        # Persist app state under the per-user data directory.
        migrate_legacy_data()
        self.filepath = get_data_file(filename)
        # Default state
        self.state = {
            "windowPos": {"x": 100, "y": 100},
            "windowSize": {"w": DEFAULT_WINDOW_WIDTH, "h": DEFAULT_WINDOW_HEIGHT},
            "pinned": False,
            "startOnBoot": False,
            "opacity": 1.0,
            "positionLocked": False,
            "alwaysOnTop": False,
            "theme": "dark",
            "taskTextSize": 14,
            "historyShortcut": "Ctrl+H",
            "settingsShortcut": "Ctrl+,",
            "pinShortcut": "Ctrl+P",
            "groupsEnabled": False,
            "lastExportDir": ""
        }
        self.app_name = "Nudge"

    @staticmethod
    def default_window_geometry() -> dict:
        """Fallback geometry when nothing is persisted yet (Stage 2 may raise defaults)."""
        return {
            "windowPos": {"x": 100, "y": 100},
            "windowSize": {"w": DEFAULT_WINDOW_WIDTH, "h": DEFAULT_WINDOW_HEIGHT},
        }

    def get_window_geometry(self) -> Tuple[int, int, int, int]:
        """Return (x, y, width, height) from persisted state."""
        defaults = self.default_window_geometry()
        pos = self.state.get("windowPos", defaults["windowPos"])
        size = self.state.get("windowSize", defaults["windowSize"])
        return (
            int(pos.get("x", 100)),
            int(pos.get("y", 100)),
            int(size.get("w", DEFAULT_WINDOW_WIDTH)),
            int(size.get("h", DEFAULT_WINDOW_HEIGHT)),
        )

    def save_window_geometry(self, x: int, y: int, width: int, height: int) -> None:
        """Persist window position and size (always saved; restore respects position lock)."""
        self.state["windowPos"] = {"x": x, "y": y}
        self.state["windowSize"] = {"w": width, "h": height}
        self.save()

    @staticmethod
    def clamp_geometry_to_screen(
        x: int,
        y: int,
        width: int,
        height: int,
        available_rect,
        min_width: int = MIN_WINDOW_WIDTH,
        min_height: int = MIN_WINDOW_HEIGHT,
    ) -> Tuple[int, int, int, int]:
        """
        Keep the window fully visible on an available screen.
        Guards against disconnected monitors leaving the window off-screen.
        """
        width = max(min_width, width)
        height = max(min_height, height)

        if available_rect is None:
            return x, y, width, height

        max_w = available_rect.width()
        max_h = available_rect.height()
        width = min(width, max_w)
        height = min(height, max_h)

        if x + width > available_rect.right():
            x = available_rect.right() - width
        if y + height > available_rect.bottom():
            y = available_rect.bottom() - height
        if x < available_rect.left():
            x = available_rect.left()
        if y < available_rect.top():
            y = available_rect.top()

        return x, y, width, height
        
    def load(self):
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    loaded_state = json.load(f)
                    self.state.update(loaded_state)
                    if isinstance(self.state.get("historyShortcuts"), list) and self.state["historyShortcuts"]:
                        self.state["historyShortcut"] = self.state["historyShortcuts"][0]
                    if isinstance(self.state.get("settingsShortcuts"), list) and self.state["settingsShortcuts"]:
                        self.state["settingsShortcut"] = self.state["settingsShortcuts"][0]
                    self.state.pop("historyShortcuts", None)
                    self.state.pop("settingsShortcuts", None)
            except (json.JSONDecodeError, OSError):
                pass
        return self.state

    def save(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4)
        except OSError:
            pass

    def set_run_on_startup(self, enable: bool):
        """
        Adds or removes the application from the Windows current user run registry.
        """
        self.state["startOnBoot"] = enable
        self.save()
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        # Build the command string. If running from source, include the python executable.
        executable_path = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        
        if script_path.endswith('.py'):
            cmd = f'"{executable_path}" "{script_path}"'
        else:
            # For packaged .exe
            cmd = f'"{executable_path}"'
            
        try:
            # Open registry key with write access
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            
            if enable:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, self.app_name)
                except FileNotFoundError:
                    # Key does not exist, nothing to delete
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Registry operation failed: {e}")
