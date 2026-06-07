# N4 — Friendly Changelog for Regular Users

## Problem
GitHub release notes are often written in developer language (issue references, technical details). Regular users need a plain-language summary of what changed.

## Files
- `C:\Users\Prosperr\Documents\_Remind\src\backend\updater.py`
- `C:\Users\Prosperr\Documents\_Remind\sprint\sprint 5\N1_tutorial_changelog.md` (integration with "What's New" popup)

---

## Solution: Two Versions of Changelog

### Option A: Structured GitHub Release Body

Write GitHub releases with a "User-friendly" section at the top:

```
## What's New in v1.1.1

**For you:**
- ✨ Auto-update: Nudge can now check for updates and install them automatically
- 🖥️ System tray: Close button minimizes to tray — right-click to quit
- 🐛 Fixed text clipping at minimum window size
- 🎨 Dark theme now applies fully when switching from Light

**For developers:**
- Implemented updater backend (#42)
- Added SystemTrayManager (#45)
- Fixed responsive_text width calculation (#38)
```

### Option B: Separate Friendly Changelog

Add a `friendly_changelog` field to `appstate.json`:

```python
"lastFriendlyChangelog": ""
```

In `updater.py:check_for_update()`, if the release body contains `---` separator, split:

```python
def parse_changelog(release_body: str) -> tuple[str, str]:
    """Return (friendly_version, full_changelog)."""
    if "---" in release_body:
        parts = release_body.split("---", 1)
        return parts[0].strip(), parts[1].strip()
    return release_body.strip(), release_body.strip()
```

Store friendly version in appstate:
```python
# In MainWindow._show_update_dialog, after fetching:
friendly, full = parse_changelog(result.changelog)
```

### Option C: Static Mapping (Simple)

For older releases, maintain a mapping in code:

```python
FRIENDLY_CHANGELOGS = {
    "1.1.0": "Initial public release with task management, groups, history, themes, and export.",
    "1.1.1": "• Auto-update: Nudge can now update itself\n"
             "• System tray: Minimize to tray instead of closing\n"
             "• Fixed: Text clipping at minimum window size\n"
             "• Fixed: Dark theme not fully applying after switching from Light",
}
```

Show in "What's New" popup:
```python
changelog = FRIENDLY_CHANGELOGS.get(__version__, "Bug fixes and improvements.")
```

## Recommendation
Use **Option A** (structured release notes) + **Option C** (static fallback map).
- Write releases with `---` separator
- Parse on fetch
- Fall back to static map if network unavailable

## Verification
- After update, "What's New" popup shows friendly language
- No developer jargon, issue numbers, or technical terms
- User can understand what changed at a glance