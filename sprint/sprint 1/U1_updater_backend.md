# U1 — Create src/backend/updater.py

## Context
- **App:** Nudge (PyInstaller-packaged Windows desktop app, Python 3 + PyQt6)
- **Version:** `src/__init__.py` has `__version__ = "1.1.0"` — next release will be `1.1.1`
- **Data dir:** `%APPDATA%\Nudge\` (via `src/backend/paths.py`)
- **Target:** GitHub Releases API for version checks

## Requirements

Create `C:\Users\Prosperr\Documents\_Remind\src\backend\updater.py` using **only stdlib** (`urllib`, `json`, `subprocess`, `tempfile`, `pathlib`, `sys`, `dataclasses`, `threading`).

### 1. Dataclass: `UpdateCheckResult`
```python
@dataclass
class UpdateCheckResult:
    available: bool = False
    latest_version: str = ""
    download_url: str = ""
    changelog: str = ""
```

### 2. `check_for_update(current_version: str, check_url: str = None, timeout: int = 10) -> UpdateCheckResult | None`
- Default `check_url`: `"https://api.github.com/repos/user/nudge/releases/latest"` (make it a module-level constant `DEFAULT_CHECK_URL` so it's easy to change)
- Fetch JSON with `urllib.request.urlopen`, headers: `Accept: application/json`, `User-Agent: Nudge/1.0`
- Parse `tag_name` (strip leading `v`), compare with `current_version` using tuple comparison: `(major, minor, patch)`
- If newer: find `.exe` asset in `assets[]` → use its `browser_download_url`; fallback to `html_url`
- Return `UpdateCheckResult(available=True, latest_version=tag, download_url=url, changelog=body)`
- If same/older: return `UpdateCheckResult(available=False)`
- On ANY network/parse error: return `None` silently (no crash, no exception)

### 3. `download_update(download_url: str, dest_dir: Path, latest_version: str, progress_callback: Callable[[int, int], None] = None) -> Path | None`
- Create `dest_dir` if needed
- Target filename: `Nudge_{latest_version}.exe`
- Stream download in 8KB chunks, write to file
- Call `progress_callback(downloaded, total)` if provided
- Timeout: 60 seconds
- On failure: delete partial file, return `None`

### 4. `_spawn_installer(downloaded_exe: Path, current_exe: Path) -> bool`
- Write PowerShell script to `downloaded_exe.parent / "install.ps1"`:
```powershell
Start-Sleep -Seconds 2
Stop-Process -Name "Nudge" -Force -ErrorAction SilentlyContinue
Copy-Item "{downloaded_exe}" "{current_exe}" -Force
Start-Process "{current_exe}"
Remove-Item "{downloaded_exe}" -Force
Remove-Item "{script_path}" -Force
```
- Launch hidden: `subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", script_path], close_fds=True)`
- Return `True`/`False`

### 5. `perform_update(download_url: str, latest_version: str) -> bool`
- Determine `current_exe`: `Path(sys.executable)` if frozen, else same
- Temp dir: `Path(tempfile.gettempdir()) / "Nudge_update"`
- Call `download_update()`, then `_spawn_installer()`
- Return `True` if both succeed

### 6. Module-level constants (easy to change later)
```python
DEFAULT_CHECK_URL = "https://api.github.com/repos/user/nudge/releases/latest"
DEFAULT_DOWNLOAD_BASE = "https://github.com/user/nudge/releases/latest/download"
```

## Verification
```python
# In Python REPL:
from src.backend.updater import check_for_update, perform_update
result = check_for_update("1.0.1")
assert result is None or isinstance(result, UpdateCheckResult)
# No crashes on network error
```

## Notes
- Version comparison: `def _parse(v): return tuple(int(x) for x in v.lstrip("vV").split(".")[:3])`
- Pad tuples to length 3: `(1, 0, 1)` vs `(1, 0, 2)`
- No external deps — must work in bundled EXE