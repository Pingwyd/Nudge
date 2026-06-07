# R1 — Verify Boot Notification Icon Path (M12)

## File to Read
`C:\Users\Prosperr\Documents\_Remind\src\backend\boot_checker.py`

## What to Check
```python
# At lines 36-45, confirm:
icon_path = ""
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    icon_path = os.path.join(sys._MEIPASS, "icon.ico")
else:
    icon_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "icon.ico",
    )
```

## Verify
- [ ] `_MEIPASS` fallback exists for PyInstaller frozen builds
- [ ] Fallback path resolves to project root for source runs
- [ ] If icon doesn't exist, `icon_path = ""` fallback handles gracefully

## Fix (only if broken)
If the path resolution is wrong, update to use `src.backend.paths` or the project root correctly:

```python
# Use paths module for consistency
from src.backend.paths import _exe_dir
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    icon_path = os.path.join(sys._MEIPASS, "icon.ico")
else:
    icon_path = str(_exe_dir() / "icon.ico")
```

## Result
Print "R1 verified" or describe the fix applied.