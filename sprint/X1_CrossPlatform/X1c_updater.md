# X1c — Updater: Cross-Platform Asset Selection & Installation

## Objective
Remove Windows-only PowerShell fallback, add macOS `.dmg` asset support, replace installer with platform-appropriate mechanism.

## Changes

### Step 1 — Edit `src/backend/updater.py`

#### 1a — Replace `_ps_fetch` and `_ps_download` (lines 57-97)

These are Windows PowerShell fallbacks for when Python's `_ssl` DLL fails. On macOS, Python's SSL works natively. Remove the PowerShell fallback entirely:

```python
# Remove functions: _ps_fetch (line 57), _ps_download (line 81)
# They are no longer needed — SSL works natively on macOS.
```

#### 1b — Update `_fetch_url` (line 42-55)

```python
def _fetch_url(url, headers, timeout=10):
    """Fetch a URL using Python's ssl/urllib. Cross-platform."""
    ctx = _get_ssl_context()
    if ctx is None:
        raise RuntimeError("SSL context unavailable — cannot make HTTPS requests")
    from urllib.request import Request, urlopen
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()
```

#### 1c — Update `check_for_update` (line 226) — cross-platform asset filter

```python
# In the asset loop, replace the .exe check with platform-aware filter:
if assets:
    ext = ".exe" if sys.platform == "win32" else ".dmg" if sys.platform == "darwin" else ".AppImage"
    for asset in assets:
        name = asset.get("name", "")
        if name.endswith(ext):
            download_url = asset.get("browser_download_url", "")
            break
    if not download_url:
        download_url = assets[0].get("browser_download_url", "")
```

Also add `import sys` at top if not already present (it is — line 6).

#### 1d — Update `download_update` (line 250) — platform-aware filename

```python
ext = ".exe" if sys.platform == "win32" else ".dmg" if sys.platform == "darwin" else ".AppImage"
dest_path = dest_dir / f"Nudge_{latest_version}{ext}"
```

Remove the PowerShell fallback block (lines 275-283). `download_update` should only use Python's urllib:

```python
def download_update(
    download_url: str,
    dest_dir: Path,
    latest_version: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Optional[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = ".exe" if sys.platform == "win32" else ".dmg" if sys.platform == "darwin" else ".AppImage"
    dest_path = dest_dir / f"Nudge_{latest_version}{ext}"

    ctx = _get_ssl_context()
    if ctx is None:
        return None

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
```

#### 1e — Replace `_spawn_installer` (line 286-305) with cross-platform version

```python
def _spawn_installer(downloaded_path: Path, current_exe: Path) -> bool:
    """Launch the downloaded installer. Platform-specific."""
    try:
        if sys.platform == "win32":
            subprocess.Popen([str(downloaded_path)], close_fds=True)
            return True
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(downloaded_path)])
            return True
        else:
            # Linux AppImage
            os.chmod(downloaded_path, 0o755)
            subprocess.Popen([str(downloaded_path)])
            return True
    except OSError:
        return False
```

#### 1f — Simplify `perform_update` (line 308-318)

```python
def perform_update(download_url: str, latest_version: str) -> bool:
    current_exe = Path(sys.executable) if getattr(sys, "frozen", False) else Path(sys.executable)
    temp_dir = Path(tempfile.gettempdir()) / "Nudge_update"
    downloaded = download_update(download_url, temp_dir, latest_version)
    if downloaded is None:
        return False
    return _spawn_installer(downloaded, current_exe)
```

### Step 2 — Clean up unused imports

Remove `import subprocess` if only used in `_spawn_installer` (keep it — still needed). Remove `shutil` if no longer used anywhere.

## Verification
- On Windows: `.exe` asset downloaded, installer launched
- On macOS: `.dmg` asset selected, `open downloaded.dmg` runs
- On Linux: `.AppImage` selected, made executable and launched
- No PowerShell dependency — works purely via Python urllib + SSL