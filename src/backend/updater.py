import json
import logging
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from src.os_layer.platform_utils import is_windows, is_macos, is_linux

DEFAULT_CHECK_URL = "https://api.github.com/repos/Pingwyd/Nudge/releases/latest"
DEFAULT_DOWNLOAD_BASE = "https://github.com/Pingwyd/Nudge/releases/latest/download"
GITHUB_REPO = "Pingwyd/Nudge"
GITHUB_RELEASES_LATEST_PAGE = f"https://github.com/{GITHUB_REPO}/releases/latest"

# Placeholder URLs from early builds/docs that were persisted in appstate.json.
_STALE_UPDATE_URL_MARKERS = (
    "/repos/user/",
    "/user/nudge",
    "your-org",
    "your-repo",
    "example.com",
)


def normalize_update_check_url(url: Optional[str]) -> str:
    """Return a usable GitHub releases API URL, replacing known bad placeholders."""
    if not url or not str(url).strip():
        return DEFAULT_CHECK_URL
    cleaned = str(url).strip()
    lowered = cleaned.lower()
    if not lowered.startswith("https://api.github.com/repos/"):
        return DEFAULT_CHECK_URL
    if any(marker in lowered for marker in _STALE_UPDATE_URL_MARKERS):
        return DEFAULT_CHECK_URL
    return cleaned


def _bare_version(version: str) -> str:
    return version.lstrip("vV")


def _release_tag(version: str) -> str:
    return f"v{_bare_version(version)}"


def _version_from_release_page_url(url: str) -> str:
    from urllib.parse import urlparse

    path = urlparse(url).path
    if "/tag/" in path:
        return _bare_version(path.rsplit("/tag/", 1)[-1])
    return ""


def build_platform_download_url(version: str) -> tuple[str, str]:
    """Build a predictable release asset URL (no GitHub API needed)."""
    bare = _bare_version(version)
    tag = _release_tag(bare)
    base = f"https://github.com/{GITHUB_REPO}/releases/download/{tag}"
    if is_windows():
        return f"{base}/Nudge-{bare}-windows.zip", "zip"
    if is_macos():
        return f"{base}/Nudge-{bare}.dmg", "dmg"
    if is_linux():
        return f"{base}/Nudge-{bare}.AppImage", "appimage"
    return "", ""


def _is_github_rate_limit_error(message: str) -> bool:
    lowered = message.lower()
    return "403" in message and (
        "rate limit" in lowered
        or "forbidden" in lowered
        or "status code 403" in lowered
    )

logging.basicConfig(
    level=logging.DEBUG,
    filename=Path(tempfile.gettempdir()) / "Nudge_update.log",
    format="%(asctime)s [%(levelname)s] %(message)s",
)

_PLATFORM_EXT = ".exe" if is_windows() else ".dmg" if is_macos() else ".AppImage"


def select_platform_asset(assets: list[dict]) -> tuple[str, str]:
    """Pick the correct platform asset. Returns (download_url, asset_kind)."""
    if is_windows():
        for asset in assets:
            name = asset.get("name", "")
            if name.endswith("-windows.zip"):
                return asset.get("browser_download_url", ""), "zip"
        for asset in assets:
            name = asset.get("name", "")
            if name.startswith("Nudge-Setup-") and name.endswith(".exe"):
                return asset.get("browser_download_url", ""), "installer"
        for asset in assets:
            if asset.get("name", "").endswith(".exe"):
                return asset.get("browser_download_url", ""), "installer"
        return "", ""

    if is_macos():
        for asset in assets:
            if asset.get("name", "").endswith(".dmg"):
                return asset.get("browser_download_url", ""), "dmg"
        return "", ""

    if is_linux():
        for asset in assets:
            if asset.get("name", "").endswith(".AppImage"):
                return asset.get("browser_download_url", ""), "appimage"
        return "", ""

    return "", ""


@dataclass
class UpdateCheckResult:
    available: bool = False
    latest_version: str = ""
    download_url: str = ""
    asset_kind: str = ""
    changelog: str = ""
    error: str = ""
    release_id: int = 0


FRIENDLY_CHANGELOGS: dict[str, str] = {
    "1.1.0": (
        "\u2728 New Features\n"
        "  \u2022 Auto-update: Nudge now checks for updates on launch\n"
        "  \u2022 System tray: app minimizes to tray instead of closing\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Fixed crash when adding tasks at minimum window width\n"
        "  \u2022 Fixed text clipping behind the Edit button\n"
        "  \u2022 Dark theme now applies consistently across all UI elements"
    ),
    "1.2.0": (
        "\u2728 New Features\n"
        "  \u2022 Tutorial dialog on first launch\n"
        "  \u2022 What\u2019s New popup after each update\n"
        "  \u2022 Support dialog with Donate button (Flutterwave)\n"
        "  \u2022 User-friendly changelog display in update dialogs\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Removed checkboxes from task rows (click text to complete)\n"
        "  \u2022 Min-width text column now spans full window width\n"
        "  \u2022 Close confirmation dialog for tray quit\n"
        "  \u2022 Overflow menu (\u00b7\u00b7\u00b7) replaces chrome buttons for cleaner title bar"
    ),
    "1.2.1": (
        "\ud83d\udcc8 Improvements\n"
        "  \u2022 Render performance: batched UI updates, debounced resize\n"
        "  \u2022 Build size reduced by excluding unused Qt modules\n"
        "  \u2022 Memory leak fixes: timer cleanup, forced GC after render\n"
        "  \u2022 End-to-end verification bundle for all phases\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Fixed text size not applying to newly added tasks\n"
        "  \u2022 Fixed Always on Top / Pin to Desktop text loss on toggle\n"
        "  \u2022 Fixed dark theme not applying to History, Settings, Export panels\n"
        "  \u2022 Fixed three-column collapse at minimum window width"
    ),
    "1.2.2": (
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Fixed theme not applying to all windows when switching back to the original theme\n"
        "  \u2022 Theme now updates instantly across all open dialogs\n"
        "\n"
        "\ud83d\udce6 Improvements\n"
        "  \u2022 Glass-themed download dialog with progress bar\n"
        "  \u2022 Threaded download (menus no longer freeze during updates)\n"
        "  \u2022 Download speed boosted with 64KB chunks"
    ),
    "1.2.3": (
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Fixed update checker failing with SSL certificate errors\n"
        "  \u2022 Better diagnostic logging for update check failures"
    ),
    "1.2.4": (
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 certifi not bundled in frozen EXE (update check always failed)\n"
        "  \u2022 _ssl DLL crash at module import (app wouldn't start)\n"
        "  \u2022 PowerShell window flashing during fallback HTTPS request\n"
        "  \u2022 ThemedMessageDialog clipped long error text\n"
        "\n"
        "\ud83d\udce6 Improvements\n"
        "  \u2022 PowerShell Invoke-WebRequest fallback when _ssl DLL is broken\n"
        "  \u2022 Logs written to %TEMP%\\Nudge_update.log for diagnostics\n"
        "  \u2022 Error dialog now shows the actual exception detail\n"
        "  \u2022 Changelog dialogs now render styled release notes"
    ),
    "1.5.0": (
        "\u2728 New Features\n"
        "  \u2022 Right-click a task to Copy its text to clipboard\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 macOS/Linux builds now work alongside Windows (cross-platform port)\n"
        "\n"
        "\ud83d\udce6 Improvements\n"
        "  \u2022 Release workflow now builds Windows, macOS, and Linux in parallel\n"
        "  \u2022 App icon now loads from .ico / .icns / .png depending on platform"
    ),
    "1.5.1": (
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Frameless windows now draggable and resizable on Linux (Wayland / WSLg)\n"
        "\n"
        "\ud83d\udce6 Improvements\n"
        "  \u2022 Linux release now includes a .deb package for Debian/Ubuntu\n"
        "  \u2022 Linux build includes icon.png so the tray icon shows correctly\n"
        "  \u2022 macOS/Linux release assets now have version and platform in the filename"
    ),
    "1.5.2": (
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Download progress bar now updates smoothly (was stuck at 0% on some machines)\n"
        "  \u2022 macOS update now kills the old app before launching the new one\n"
        "  \u2022 Linux AppImage update now copies to ~/.local/bin/nudge so it persists after temp cleanup\n"
        "  \u2022 Fixed Content-Length parsing crash when header is empty"
    ),
    "1.6.0": (
        "\ud83c\udf89 Task-Specific Reminders\n"
        "  \u2022 Right-click any task to set a reminder (15m, 30m, 1h, 2h, or custom time)\n"
        "  \u2022 Custom duration input: just type \"25 minutes\" or \"2 hours\"\n"
        "  \u2022 View and manage pending task reminders in Settings \u2192 Advanced\n"
        "\n"
        "\ud83d\udce6 Dialogs & Theme\n"
        "  \u2022 Reminder dialogs now use the app\u2019s glass-panel style\n"
        "  \u2022 Calendar popup follows dark and light themes\n"
        "  \u2022 Edit timer form redesigned for better readability\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 \u201cAlways on Top\u201d / \u201cPin to Desktop\u201d now work immediately after saving, no restart needed\n"
        "  \u2022 Info dialogs (like \u201cYou\u2019re up to date\u201d) no longer block the app \u2014 click outside to close"
    ),
    "1.6.1": (
        "\ud83d\udce6 Improvements\n"
        "  \u2022 History window is now resizable \u2014 drag any edge or corner\n"
        "  \u2022 Settings window is now resizable and remembers its size\n"
        "  \u2022 History window remembers its size between sessions\n"
        "  \u2022 Main window starts smaller (300\u00d7300) for a compact widget feel\n"
        "  \u2022 Update download now retries once and falls back to PowerShell if SSL fails\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Settings sidebar text no longer clipped (sidebar button size fixed)\n"
        "  \u2022 Glass panels are more opaque \u2014 no more text bleeding through from behind\n"
        "  \u2022 \u201cYou\u2019re up to date\u201d popup is more compact (350\u00d7150)\n"
        "  \u2022 Update download no longer silently fails on SSL errors \u2014 shows the real error"
    ),
    "1.7.0": (
        "\ud83d\udce6 Unified Dialog System\n"
        "  \u2022 All popups now use a shared glass-panel base \u2014 consistent look, faster updates\n"
        "  \u2022 History, Settings, and Tutorial windows share the same drag/resize behavior\n"
        "\n"
        "\ud83d\udcd6 Tutorial Revamped\n"
        "  \u2022 Welcome guide is now paginated into 6 focused pages with Prev/Next navigation\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Eliminated ~400 lines of duplicated frameless-window setup across all dialogs"
    ),
    "1.10.0": (
        "\ud83e\uddfa Drag to Reorder Groups\n"
        "  \u2022 Drag a group\u2019s header bar to rearrange your task groups in any order\n"
        "  \u2022 A blue line shows exactly where the group will land\n"
        "  \u2022 Drag a group into Notepad to paste its name and task list as plain text\n"
        "\n"
        "\U0001f50d History Improvements\n"
        "  \u2022 Search bar in History \u2014 type to filter archived tasks live\n"
        "  \u2022 Toggle \u201cDon\u2019t ask to delete\u201d to skip confirmation when clearing history\n"
        "  \u2022 Clear All button to archive everything in one click\n"
        "\n"
        "\ud83d\udcfd Other Improvements\n"
        "  \u2022 Undo toast now has a \u2716 dismiss button to close without undoing\n"
        "  \u2022 Input bars scroll sideways for long task text\n"
        "  \u2022 Undo popup is wider so messages fit better"
    ),
    "1.11.0": (
        "\u2728 Liquid Glass Aesthetic\n"
        "  \u2022 Frosted glass panels now have subtle drop shadows and glow effects\n"
        "  \u2022 Mouse-following glass shine over the task list (toggle in Settings)\n"
        "  \u2022 Crisp SVG icons for Settings and History in the title bar\n"
        "  \u2022 Input fields glow with your accent color when focused\n"
        "\n"
        "\ud83d\udc1b Live Settings\n"
        "  \u2022 Opacity, text size, and mouse glow now apply instantly as you adjust\n"
        "  \u2022 Task text size changes apply to all rows without clicking Save\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Liquid glass transparency now applies on first launch\n"
        "  \u2022 Window corners no longer show black box edges on startup"
    ),
    "1.12.0": (
        "\u2728 Update Improvements\n"
        "  \u2022 Download now runs in the background \u2014 you can keep working while it downloads\n"
        "  \u2022 After download, choose \u201cInstall Now\u201d or \u201cRemind Me Later\u201d\n"
        "  \u2022 Cached downloads: if you delay, the next check skips re-downloading\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Progress bar no longer stays stuck at 0%\n"
        "  \u2022 Fixed file lock errors when retrying a failed download\n"
        "  \u2022 PowerShell download now shows progress instead of blocking\n"
        "  \u2022 Progress bar no longer cycles back to 0% after 100MB"
    ),
    "1.13.0": (
        "\u2705 Task Area Redesign\n"
        "  \u2022 Checkboxes to mark tasks complete\n"
        "  \u2022 Due dates with colored chips\n"
        "  \u2022 Priority indicators (High priority shows red)\n"
        "  \u2022 Tags with 8-color palette picker\n"
        "  \u2022 Recurring tasks (daily, weekly, monthly)\n"
        "  \u2022 Tag filter dropdown in title bar\n"
        "\n"
        "\ud83d\udce6 Settings & Polish\n"
        "  \u2022 Font selection for task text\n"
        "  \u2022 History retention setting (5 days to Forever)\n"
        "  \u2022 Reminders popup (Alt+R)\n"
        "  \u2022 Footer bar with task count and History shortcut\n"
        "  \u2022 Button styles unified across all dialogs\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Dropdown menus now inherit theme colors properly\n"
        "  \u2022 Tag color picker closes when clicking outside\n"
        "  \u2022 Crash dialog emoji no longer clipped\n"
        "  \u2022 Settings remembers last tab\n"
        "  \u2022 Badges no longer clip at minimum window size\n"
        "  \u2022 Glass panel drag is now smoother"
    ),
    "1.14.0": (
        "\u2728 New Features\n"
        "  \u2022 Flat list priority view with HIGH PRIORITY header and divider\n"
        "  \u2022 Drag-and-drop import \u2014 drop text, URLs, or files to create tasks\n"
        "  \u2022 Drop indicator overlay shows the drop zone during drag\n"
        "\n"
        "\ud83d\udce6 Improvements\n"
        "  \u2022 History shortcut (Ctrl+H) now toggles \u2014 closes dialog if open\n"
        "  \u2022 Reminders shortcut (Alt+R) configurable in Settings\n"
        "  \u2022 Footer restyled with visible border and theme-aware colors\n"
        "  \u2022 Shortcut suppression only applies when input bar has focus\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 History shortcut no longer blocked by dialog search bars\n"
        "  \u2022 Reminders dialog no longer stacks on repeated presses\n"
        "  \u2022 Footer border visible in all themes (dark, light, OLED)\n"
        "  \u2022 Footer task count readable in light mode"
    ),
    "2.0.0": (
        "\u2728 New Features\n"
        "  \u2022 Clipboard import \u2014 Ctrl+Shift+V to paste multiple tasks at once\n"
        "  \u2022 Completion sound effects (toggle in Settings \u2192 Sound)\n"
        "  \u2022 Stats bar in History \u2014 total, today, and yesterday counts\n"
        "  \u2022 Card-style task rows in History with rounded corners\n"
        "  \u2022 Collapse chevrons on History time period sections\n"
        "  \u2022 Ctrl+F to focus the tag filter dropdown\n"
        "  \u2022 Real-time task search from the title bar\n"
        "\n"
        "\ud83d\udce6 Improvements\n"
        "  \u2022 History sorted most-recent-first within each time period\n"
        "  \u2022 Smaller, better-proportioned buttons in confirmation dialogs\n"
        "  \u2022 20 UI files cleaned up with centralized constants\n"
        "  \u2022 Bold divider after last high-priority task\n"
        "  \u2022 HIGH PRIORITY header auto-removes when all tasks completed\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 History count badge updates on delete\n"
        "  \u2022 History tab updates live when tasks completed while open\n"
        "  \u2022 Footer task count updates on task add/remove\n"
        "  \u2022 Confirmation dialog buttons no longer clipped\n"
        "  \u2022 Group dropdown populates correctly on restart"
    ),
    "2.0.1": (
        "\u2728 New Features\n"
        "  \u2022 Task search bar \u2014 Ctrl+F with scope filters for tasks, groups, and tags\n"
        "  \u2022 Tray quick-add \u2014 add tasks from the system tray menu\n"
        "  \u2022 Dim overlay for search and modal focus states\n"
        "\n"
        "\ud83d\udce6 Improvements\n"
        "  \u2022 Faster theme and settings appearance changes\n"
        "  \u2022 Smoother window resize (deferred text reflow)\n"
        "  \u2022 Debounced disk writes for tasks and app state\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Pin to desktop survives Win+D and HWND recreation\n"
        "  \u2022 Tray toggle hotkey works after layer changes\n"
        "  \u2022 Flat view shows tasks on first boot\n"
        "  \u2022 No ghost window frames at startup\n"
        "  \u2022 Group search filters tasks in-place per group"
    ),
    "2.0.2": (
        "\ud83d\udce6 Release\n"
        "  \u2022 Complete build shipping all 2.0.1 features and fixes\n"
        "  \u2022 Replaces the incomplete v2.0.1 release tag\n"
        "\n"
        "\u2728 New Features\n"
        "  \u2022 Task search bar \u2014 Ctrl+F with scope filters\n"
        "  \u2022 Tray quick-add from the system tray menu\n"
        "  \u2022 Dim overlay for search and modal focus\n"
        "\n"
        "\ud83d\udce6 Improvements\n"
        "  \u2022 Faster theme and settings changes\n"
        "  \u2022 Smoother window resize\n"
        "  \u2022 Debounced disk writes\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Pin to desktop, hotkeys, flat-view boot, ghost frames, group search"
    ),
    "2.0.3": (
        "\ud83d\udce6 Improvements\n"
        "  \u2022 Update check and download use Qt networking (more reliable on Windows)\n"
        "  \u2022 Windows in-place updates extract the release zip instead of overwriting the exe\n"
        "\n"
        "\ud83d\udc1b Bug Fixes\n"
        "  \u2022 Fixed empty or invalid GitHub API responses crashing the update check\n"
        "  \u2022 Fixed update dialog crash (missing FONT_SIZE_BODY import)\n"
        "  \u2022 Fixed Windows update installing the wrong file type"
    ),
}


def parse_changelog(release_body: str, version: str = "") -> tuple[str, str]:
    """Return (friendly_version, full_changelog) split on ---."""
    if version in FRIENDLY_CHANGELOGS:
        return FRIENDLY_CHANGELOGS[version], release_body.strip()
    if "---" in release_body:
        parts = release_body.split("---", 1)
        return parts[0].strip(), parts[1].strip()
    return release_body.strip(), release_body.strip()


def _parse_version(version_str: str) -> tuple:
    cleaned = version_str.lstrip("vV")
    parts = []
    for part in cleaned.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def check_for_update_from_body(body: bytes, current_version: str) -> UpdateCheckResult:
    if not body or not body.strip():
        return UpdateCheckResult(error="Empty response from update server")
    try:
        data = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        return UpdateCheckResult(error=f"Invalid update response: {exc}")

    tag = data.get("tag_name", "")
    latest = _parse_version(tag)
    current = _parse_version(current_version)
    release_id = data.get("id", 0)

    if latest <= current:
        return UpdateCheckResult(available=False, release_id=release_id)

    download_url = ""
    asset_kind = ""
    assets = data.get("assets", [])
    if assets:
        download_url, asset_kind = select_platform_asset(assets)
    if not download_url:
        download_url = data.get("html_url", "")

    return UpdateCheckResult(
        available=True,
        latest_version=tag.lstrip("vV"),
        download_url=download_url,
        asset_kind=asset_kind,
        changelog=data.get("body", ""),
        release_id=release_id,
    )


def check_for_update_from_redirect(
    final_url: str,
    current_version: str,
) -> UpdateCheckResult:
    """Resolve latest version from /releases/latest redirect (no API quota)."""
    latest_version = _version_from_release_page_url(final_url)
    if not latest_version:
        return UpdateCheckResult(
            error=f"Could not parse release version from {final_url}",
        )

    latest = _parse_version(latest_version)
    current = _parse_version(current_version)
    if latest <= current:
        return UpdateCheckResult(available=False)

    download_url, asset_kind = build_platform_download_url(latest_version)
    if not download_url:
        return UpdateCheckResult(error="No download URL for this platform")

    return UpdateCheckResult(
        available=True,
        latest_version=latest_version,
        download_url=download_url,
        asset_kind=asset_kind,
        changelog=FRIENDLY_CHANGELOGS.get(latest_version, ""),
    )


def check_for_update(
    current_version: str,
    check_url: Optional[str] = None,
    timeout: int = 10,
) -> UpdateCheckResult:
    url = normalize_update_check_url(check_url)
    try:
        from src.backend.update_client import (
            UpdateHttpError,
            fetch_bytes,
            fetch_final_url,
            github_headers,
        )

        body = fetch_bytes(url, github_headers(), timeout_ms=timeout * 1000)
        return check_for_update_from_body(body, current_version)
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        logging.warning("API update check failed: %s", err)
        if _is_github_rate_limit_error(err) or "403" in err:
            try:
                final_url = fetch_final_url(
                    GITHUB_RELEASES_LATEST_PAGE,
                    github_headers(),
                    timeout_ms=timeout * 1000,
                )
                logging.info("Fell back to release page redirect: %s", final_url)
                return check_for_update_from_redirect(final_url, current_version)
            except Exception as fallback_exc:
                logging.error("Redirect update check failed: %s", fallback_exc)
                return UpdateCheckResult(
                    error=(
                        "GitHub API rate limit exceeded. "
                        f"Fallback check also failed: {fallback_exc}"
                    ),
                )
        logging.error("Update check failed: %s", err)
        return UpdateCheckResult(error=err)


def _download_dest_path(dest_dir: Path, latest_version: str, asset_kind: str) -> Path:
    if asset_kind == "zip":
        return dest_dir / f"Nudge-{latest_version}-windows.zip"
    if asset_kind == "installer":
        return dest_dir / f"Nudge-Setup-{latest_version}.exe"
    if asset_kind == "dmg":
        return dest_dir / f"Nudge-{latest_version}.dmg"
    if asset_kind == "appimage":
        return dest_dir / f"Nudge-{latest_version}.AppImage"
    return dest_dir / f"Nudge_{latest_version}{_PLATFORM_EXT}"


def download_update(
    download_url: str,
    dest_dir: Path,
    latest_version: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    asset_kind: str = "",
) -> tuple[Optional[Path], str]:
    """Download the update asset. Returns (path, error_msg)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    for stale in dest_dir.glob("Nudge*"):
        try:
            if stale.is_file():
                stale.unlink(missing_ok=True)
        except OSError:
            pass

    dest_path = _download_dest_path(dest_dir, latest_version, asset_kind)
    try:
        from src.backend.update_client import UpdateHttpError, download_file, github_headers

        download_file(
            download_url,
            dest_path,
            progress_callback=progress_callback,
            headers=github_headers(),
        )
        return (dest_path, "")
    except Exception as exc:
        logging.error("Download failed: %s: %s", type(exc).__name__, exc)
        if dest_path.exists():
            dest_path.unlink(missing_ok=True)
        return (None, f"{type(exc).__name__}: {exc}")


def perform_update(
    download_url: str,
    latest_version: str,
    asset_kind: str = "",
) -> bool:
    if not getattr(sys, "frozen", False):
        logging.warning("Not a frozen app — skipping update install (dev mode)")
        return True
    current_exe = Path(sys.executable)
    temp_dir = Path(tempfile.gettempdir()) / "Nudge_update"
    downloaded, err = download_update(
        download_url, temp_dir, latest_version, asset_kind=asset_kind,
    )
    if downloaded is None:
        logging.error("Update download failed: %s", err)
        return False
    return _install_update(downloaded, current_exe)


def _install_update(downloaded: Path, current_exe: Path) -> bool:
    """Run the platform-appropriate installer for the downloaded asset."""
    if is_windows():
        if downloaded.suffix.lower() == ".zip":
            return _install_zip_windows(downloaded, current_exe)
        if downloaded.suffix.lower() == ".exe":
            return _spawn_setup_installer(downloaded)
        return False
    if is_macos():
        return _install_dmg(downloaded, current_exe)
    if is_linux():
        return _install_appimage(downloaded)
    return False


def _install_zip_windows(zip_path: Path, current_exe: Path) -> bool:
    """Extract a release zip over the current onedir install folder."""
    extract_dir = Path(tempfile.mkdtemp(prefix="nudge_update_"))
    app_dir = current_exe.parent
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
        for item in extract_dir.iterdir():
            dest = app_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        return _spawn_restart_windows(current_exe)
    except (OSError, zipfile.BadZipFile) as exc:
        logging.error("Zip install failed: %s", exc)
        return False
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def _spawn_restart_windows(current_exe: Path) -> bool:
    bat_path = Path(tempfile.gettempdir()) / "nudge_restart.bat"
    bat_content = (
        "@echo off\r\n"
        "timeout /t 2 /nobreak >nul\r\n"
        "taskkill /IM Nudge.exe /F >nul 2>&1\r\n"
        f'start "" "{current_exe}"\r\n'
        'del "%~f0"\r\n'
    )
    try:
        bat_path.write_text(bat_content, encoding="utf-8")
        subprocess.Popen(
            ["cmd", "/c", str(bat_path)],
            close_fds=True,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        )
        return True
    except OSError:
        return False


def _spawn_setup_installer(setup_exe: Path) -> bool:
    try:
        subprocess.Popen(
            [str(setup_exe), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
            close_fds=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True
    except OSError:
        return False


def _install_dmg(dmg_path: Path, current_exe: Path) -> bool:
    """Mount a .dmg, copy the .app bundle over the existing one, kill the old app, launch the new one."""
    import plistlib
    mount_point = Path(tempfile.mkdtemp(prefix="nudge_mount_"))
    try:
        subprocess.run(
            ["hdiutil", "attach", str(dmg_path), "-mountpoint", str(mount_point)],
            check=True, capture_output=True, timeout=60,
        )
        app_bundles = list(mount_point.glob("*.app"))
        if not app_bundles:
            logging.error("No .app bundle found inside the DMG")
            return False
        src_app = app_bundles[0]
        dest_app = current_exe.parent / src_app.name
        if dest_app.exists():
            subprocess.run(["killall", src_app.stem], check=False, timeout=10)
            shutil.rmtree(dest_app)
        shutil.copytree(src_app, dest_app)
        subprocess.run(["open", str(dest_app)], check=False)
        return True
    except (subprocess.CalledProcessError, OSError, shutil.Error) as exc:
        logging.error("DMG install failed: %s", exc)
        return False
    finally:
        subprocess.run(["hdiutil", "detach", str(mount_point)], check=False, timeout=30)


def _install_appimage(appimage_path: Path) -> bool:
    """Copy the AppImage to a persistent location, make executable, and launch it."""
    dest = Path.home() / ".local" / "bin" / "nudge"
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(appimage_path, dest)
        st = dest.stat()
        dest.chmod(st.st_mode | stat.S_IEXEC)
        subprocess.Popen([str(dest)], close_fds=True)
        return True
    except OSError as exc:
        logging.error("AppImage launch failed: %s", exc)
        return False
