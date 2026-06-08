# X1d — UI Files: Replace `os.startfile` with Cross-Platform Call

## Objective
Replace all direct `os.startfile()` calls with the cross-platform `open_file_explorer()` helper.

## Changes

### Step 1 — Edit `src/frontend/export_dialog.py` (line 310)

```python
# Old (line 309-310):
import os
os.startfile(str(path.parent))

# New:
from src.os_layer.platform_utils import open_file_explorer
open_file_explorer(path.parent)
```

Move the import to the top of the file.

### Step 2 — Edit `src/frontend/main_window.py` (line 1327)

Inside `SettingsDialog._run_settings_export`:

```python
# Old:
import os
os.startfile(str(path.parent))

# New:
from src.os_layer.platform_utils import open_file_explorer
open_file_explorer(path.parent)
```

### Step 3 — Edit `src/frontend/main_window.py` (line ~2935)

Inside `_open_feedback_dialog`, the `os.startfile(gmail_uri)` fallback. Replace the entire platform-conditional block:

```python
# Old (lines ~2929-2935):
opened = webbrowser.open(gmail_uri)
if not opened and sys.platform == "win32":
    try:
        import os
        os.startfile(gmail_uri)
        opened = True
    except Exception:
        pass

# New:
from src.os_layer.platform_utils import open_url
open_url(gmail_uri)
```

### Step 4 — Edit `src/frontend/crash_dialog.py` (line 93-98)

Same pattern — replace the `os.startfile` fallback:

```python
# Old (lines 92-99):
opened = webbrowser.open(gmail_uri)
if not opened and sys.platform == "win32":
    try:
        import os
        os.startfile(gmail_uri)
        opened = True
    except Exception:
        pass

# New:
from src.os_layer.platform_utils import open_url
open_url(gmail_uri)
```

## Verification
- On Windows: file explorer opens, Gmail URI opens in browser
- On macOS: `open /path/to/folder` runs Finder, `open url` opens browser
- On Linux: `xdg-open` handles both
- No `os.startfile` calls remain anywhere in the codebase