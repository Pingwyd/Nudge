import json
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    import winreg
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
            "lastExportDir": "",
            "checkForUpdates": True,
            "updateCheckUrl": "https://api.github.com/repos/Pingwyd/Nudge/releases/latest",
            "lastSeenVersion": "",
            "lastChangelog": ""
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
        Adds or removes the application from OS startup.
        Windows: CurrentUser Run registry.
        macOS: LaunchAgents plist.
        Linux: autostart .desktop file.
        """
        self.state["startOnBoot"] = enable
        self.save()
        if sys.platform == "win32":
            self._set_run_on_startup_windows(enable)
        elif sys.platform == "darwin":
            self._set_run_on_startup_macos(enable)
        else:
            self._set_run_on_startup_linux(enable)

    def _app_command(self) -> str:
        """Build the command string for the current executable."""
        if sys.platform == "darwin":
            if getattr(sys, "frozen", False):
                bundle = Path(sys.executable).parent.parent
                return str(bundle)
            return f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
        if sys.platform == "win32":
            executable_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            if script_path.endswith(".py"):
                pythonw = executable_path.replace("python.exe", "pythonw.exe")
                if os.path.exists(pythonw):
                    executable_path = pythonw
                return f'"{executable_path}" "{script_path}"'
            return f'"{executable_path}"'
        return f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

    def _set_run_on_startup_windows(self, enable: bool):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, self._app_command())
            else:
                try:
                    winreg.DeleteValue(key, self.app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Registry operation failed: {e}")

    def _set_run_on_startup_macos(self, enable: bool):
        plist_dir = Path.home() / "Library" / "LaunchAgents"
        plist_dir.mkdir(parents=True, exist_ok=True)
        plist_path = plist_dir / f"com.{self.app_name}.plist"
        if enable:
            app_path = self._app_command()
            if app_path.endswith(".app"):
                prog_args = f"""    <array>
        <string>/usr/bin/open</string>
        <string>{app_path}</string>
    </array>"""
            else:
                prog_args = f"""    <array>
        <string>{sys.executable}</string>
        <string>{os.path.abspath(sys.argv[0])}</string>
    </array>"""
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.app_name}</string>
    <key>ProgramArguments</key>
{prog_args}
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
            plist_path.write_text(plist_content, encoding="utf-8")
        else:
            plist_path.unlink(missing_ok=True)

    def _set_run_on_startup_linux(self, enable: bool):
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_path = autostart_dir / f"{self.app_name}.desktop"
        if enable:
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Exec={self._app_command()}
X-GNOME-Autostart-enabled=true
"""
            desktop_path.write_text(desktop_content, encoding="utf-8")
        else:
            desktop_path.unlink(missing_ok=True)
