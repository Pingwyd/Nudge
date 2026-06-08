# X1b — State Manager: macOS Startup on Login

## Objective
Guard `import winreg` behind platform check. Add macOS launch-on-login via `LaunchAgents` plist.

## Changes

### Step 1 — Guard `import winreg` in `src/backend/state_manager.py:3`

Replace the top-level import:

```python
# Old (line 3):
import winreg

# New:
if sys.platform == "win32":
    import winreg
```

### Step 2 — Refactor `set_run_on_startup` (line 136-173) to be cross-platform

```python
def set_run_on_startup(self, enable: bool):
    self.state["startOnBoot"] = enable
    self.save()

    if sys.platform == "win32":
        self._set_run_on_startup_windows(enable)
    elif sys.platform == "darwin":
        self._set_run_on_startup_macos(enable)
    # Linux: no-op (systemd not implemented)

def _set_run_on_startup_windows(self, enable: bool):
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    executable_path = sys.executable
    script_path = os.path.abspath(sys.argv[0])

    if script_path.endswith('.py'):
        pythonw = executable_path.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            executable_path = pythonw
        cmd = f'"{executable_path}" "{script_path}"'
    else:
        cmd = f'"{executable_path}"'

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        if enable:
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, self.app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Registry operation failed: {e}")

def _set_run_on_startup_macos(self, enable: bool):
    """Create/remove a LaunchAgents plist for auto-start on login."""
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"com.{self.app_name}.plist"
    if enable:
        executable = sys.executable
        script = os.path.abspath(sys.argv[0])
        if script.endswith('.py'):
            args = [executable, script]
        else:
            args = [executable]

        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.app_name}</string>
    <key>ProgramArguments</key>
    <array>
{"".join(f'        <string>{a}</string>\n' for a in args)}    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
        try:
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            plist_path.write_text(plist_content, encoding="utf-8")
        except OSError as e:
            print(f"LaunchAgent creation failed: {e}")
    else:
        try:
            if plist_path.exists():
                plist_path.unlink()
        except OSError as e:
            print(f"LaunchAgent removal failed: {e}")
```

### Step 3 — Ensure `sys` is already imported at top

Already imported at line 5 in state_manager.py — confirmed.

## Verification
- On Windows: `set_run_on_startup(True)` adds registry key as before
- On macOS: `set_run_on_startup(True)` creates `~/Library/LaunchAgents/com.Nudge.plist`
- On macOS: `set_run_on_startup(False)` removes the plist
- On Linux: no-op, no crash
- `import winreg` only runs on Windows — no ImportError on macOS