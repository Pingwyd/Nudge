import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

DEFAULT_CHECK_URL = "https://api.github.com/repos/Pingwyd/Nudge/releases/latest"
DEFAULT_DOWNLOAD_BASE = "https://github.com/Pingwyd/Nudge/releases/latest/download"

logging.basicConfig(
    level=logging.DEBUG,
    filename=Path(tempfile.gettempdir()) / "Nudge_update.log",
    format="%(asctime)s [%(levelname)s] %(message)s",
)

_ssl_context = None

def _get_ssl_context():
    global _ssl_context
    if _ssl_context is not None:
        return _ssl_context
    import ssl
    try:
        import certifi
        _ssl_context = ssl.create_default_context(cafile=certifi.where())
        logging.debug("SSL context using certifi CA: %s", certifi.where())
    except Exception:
        _ssl_context = ssl.create_default_context()
        logging.debug("SSL context using system default CA store")
    return _ssl_context


@dataclass
class UpdateCheckResult:
    available: bool = False
    latest_version: str = ""
    download_url: str = ""
    changelog: str = ""
    error: str = ""


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
        "  \u2022 download_update missing SSL context\n"
        "\n"
        "\ud83d\udce6 Improvements\n"
        "  \u2022 Logs written to %TEMP%\\Nudge_update.log for diagnostics\n"
        "  \u2022 Error dialog now shows the actual exception detail"
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


def check_for_update(
    current_version: str,
    check_url: Optional[str] = None,
    timeout: int = 10,
) -> Optional[UpdateCheckResult]:
    url = check_url or DEFAULT_CHECK_URL
    try:
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "Nudge/1.0"})
        with urlopen(req, timeout=timeout, context=_get_ssl_context()) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        logging.error("Update check failed: %s: %s", type(exc).__name__, exc)
        return UpdateCheckResult(error=f"{type(exc).__name__}: {exc}")

    tag = data.get("tag_name", "")
    latest = _parse_version(tag)
    current = _parse_version(current_version)

    if latest <= current:
        return UpdateCheckResult(available=False)

    download_url = ""
    assets = data.get("assets", [])
    if assets:
        for asset in assets:
            name = asset.get("name", "")
            if name.endswith(".exe"):
                download_url = asset.get("browser_download_url", "")
                break
        if not download_url:
            download_url = assets[0].get("browser_download_url", "")
    if not download_url:
        download_url = data.get("html_url", "")

    return UpdateCheckResult(
        available=True,
        latest_version=tag.lstrip("vV"),
        download_url=download_url,
        changelog=data.get("body", ""),
    )


def download_update(
    download_url: str,
    dest_dir: Path,
    latest_version: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Optional[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"Nudge_{latest_version}.exe"

    try:
        req = Request(download_url, headers={"User-Agent": "Nudge/1.0"})
        with urlopen(req, timeout=60, context=_get_ssl_context()) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total:
                        progress_callback(downloaded, total)
        return dest_path
    except (URLError, HTTPError, OSError) as exc:
        logging.error("Download failed: %s: %s", type(exc).__name__, exc)
        if dest_path.exists():
            dest_path.unlink()
        return None


def _spawn_installer(downloaded_exe: Path, current_exe: Path) -> bool:
    temp_dir = downloaded_exe.parent
    script_path = temp_dir / "install.ps1"

    ps_script = f"""Start-Sleep -Seconds 2
Stop-Process -Name "Nudge" -Force -ErrorAction SilentlyContinue
Copy-Item "{downloaded_exe}" "{current_exe}" -Force
Start-Process "{current_exe}"
Remove-Item "{downloaded_exe}" -Force
Remove-Item "{script_path}" -Force
"""
    try:
        script_path.write_text(ps_script, encoding="utf-8")
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
            close_fds=True,
        )
        return True
    except OSError:
        return False


def perform_update(download_url: str, latest_version: str) -> bool:
    if getattr(sys, "frozen", False):
        current_exe = Path(sys.executable)
    else:
        current_exe = Path(sys.executable)

    temp_dir = Path(tempfile.gettempdir()) / "Nudge_update"
    downloaded = download_update(download_url, temp_dir, latest_version)
    if downloaded is None:
        return False
    return _spawn_installer(downloaded, current_exe)
