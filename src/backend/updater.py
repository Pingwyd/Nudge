import json
import logging
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional
from urllib.error import URLError, HTTPError

from src.os_layer.platform_utils import is_windows, is_macos, is_linux

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
    try:
        import ssl
        try:
            import certifi
            _ssl_context = ssl.create_default_context(cafile=certifi.where())
            logging.debug("SSL context using certifi CA: %s", certifi.where())
        except Exception:
            _ssl_context = ssl.create_default_context()
            logging.debug("SSL context using system default CA store")
    except Exception:
        _ssl_context = None
    return _ssl_context

def _fetch_url(url, headers, timeout=10):
    """Fetch a URL, returning response bytes.

    Uses Python's ssl/urllib when available; falls back to PowerShell
    Invoke-WebRequest when the _ssl C extension DLL cannot load in a
    frozen PyInstaller EXE.
    """
    ctx = _get_ssl_context()
    if ctx is not None:
        from urllib.request import Request, urlopen
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()
    return _ps_fetch(url, headers, timeout)

def _ps_fetch(url, headers, timeout):
    """Fallback HTTPS GET via PowerShell — Windows only."""
    if not is_windows():
        raise RuntimeError("PowerShell fallback is Windows-only")
    hdr = "@{" + ";".join(f'"{k}"="{v}"' for k, v in headers.items()) + "}"
    ps = (
        "$r = Invoke-WebRequest -Uri '{}' -Headers {} -TimeoutSec {} -UseBasicParsing;"
        "$b = [System.Text.Encoding]::UTF8.GetBytes($r.Content);"
        "$s = [System.Console]::OpenStandardOutput();"
        "$s.Write($b, 0, $b.Length); $s.Close()"
    ).format(url.replace("'", "''"), hdr, timeout)
    _ps_flags = subprocess.CREATE_NO_WINDOW
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True, timeout=timeout + 5, creationflags=_ps_flags,
    )
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(err or "PowerShell request failed")
    return result.stdout


def _ps_download(url, dest_path, timeout=120):
    """Fallback file download via PowerShell — Windows only."""
    if not is_windows():
        raise RuntimeError("PowerShell download fallback is Windows-only")
    ps = (
        "$r = Invoke-WebRequest -Uri '{}' -Headers @{{\"User-Agent\"=\"Nudge/1.0\"}} "
        "-TimeoutSec {} -OutFile '{}' -UseBasicParsing"
    ).format(url.replace("'", "''"), timeout, str(dest_path).replace("'", "''"))
    _ps_flags = subprocess.CREATE_NO_WINDOW
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        capture_output=True, timeout=timeout + 30, creationflags=_ps_flags,
    )
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(err or "PowerShell download failed")
    if not dest_path.exists():
        raise RuntimeError("PowerShell download created no output file")


_PLATFORM_EXT = ".exe" if is_windows() else ".dmg" if is_macos() else ".AppImage"


def select_platform_asset(assets: list[dict]) -> str:
    """Pick the correct platform installer asset from a release asset list."""
    ext = _PLATFORM_EXT
    candidates = [a for a in assets if a.get("name", "").endswith(ext)]
    if candidates:
        return candidates[0].get("browser_download_url", "")
    return ""


@dataclass
class UpdateCheckResult:
    available: bool = False
    latest_version: str = ""
    download_url: str = ""
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
        body = _fetch_url(url, {"Accept": "application/json", "User-Agent": "Nudge/1.0"}, timeout)
        data = json.loads(body.decode("utf-8"))
    except Exception as exc:
        logging.error("Update check failed: %s: %s", type(exc).__name__, exc)
        return UpdateCheckResult(error=f"{type(exc).__name__}: {exc}")

    tag = data.get("tag_name", "")
    latest = _parse_version(tag)
    current = _parse_version(current_version)
    release_id = data.get("id", 0)

    if latest <= current:
        return UpdateCheckResult(available=False, release_id=release_id)

    download_url = ""
    assets = data.get("assets", [])
    if assets:
        download_url = select_platform_asset(assets)
    if not download_url:
        download_url = data.get("html_url", "")

    return UpdateCheckResult(
        available=True,
        latest_version=tag.lstrip("vV"),
        download_url=download_url,
        changelog=data.get("body", ""),
        release_id=release_id,
    )


def download_update(
    download_url: str,
    dest_dir: Path,
    latest_version: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Optional[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = _PLATFORM_EXT
    dest_path = dest_dir / f"Nudge_{latest_version}{ext}"

    ctx = _get_ssl_context()
    if ctx is not None:
        try:
            from urllib.request import Request, urlopen
            req = Request(download_url, headers={"User-Agent": "Nudge/1.0"})
            with urlopen(req, timeout=60, context=ctx) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                with open(dest_path, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)
            return dest_path
        except (URLError, HTTPError, OSError) as exc:
            logging.error("Download failed: %s: %s", type(exc).__name__, exc)
            if dest_path.exists():
                dest_path.unlink()
            return None
    # Fallback via PowerShell when _ssl DLL is broken
    try:
        _ps_download(download_url, dest_path, timeout=120)
        return dest_path
    except Exception as exc:
        logging.error("PowerShell download failed: %s: %s", type(exc).__name__, exc)
        if dest_path.exists():
            dest_path.unlink()
        return None


def perform_update(download_url: str, latest_version: str) -> bool:
    current_exe = Path(sys.executable)
    temp_dir = Path(tempfile.gettempdir()) / "Nudge_update"
    downloaded = download_update(download_url, temp_dir, latest_version)
    if downloaded is None:
        return False
    return _install_update(downloaded, current_exe)


def _install_update(downloaded: Path, current_exe: Path) -> bool:
    """Run the platform-appropriate installer for the downloaded asset."""
    if is_windows():
        return _spawn_installer(downloaded, current_exe)
    if is_macos():
        return _install_dmg(downloaded, current_exe)
    if is_linux():
        return _install_appimage(downloaded)
    return False


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


def _install_dmg(dmg_path: Path, current_exe: Path) -> bool:
    """Mount a .dmg, copy the .app bundle over the existing one, then unmount."""
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
    """Make the .AppImage executable and launch it."""
    try:
        st = appimage_path.stat()
        appimage_path.chmod(st.st_mode | stat.S_IEXEC)
        subprocess.Popen([str(appimage_path)], close_fds=True)
        return True
    except OSError as exc:
        logging.error("AppImage launch failed: %s", exc)
        return False
