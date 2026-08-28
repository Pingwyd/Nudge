#!/usr/bin/env python3
"""Manual updater smoke test — no need to edit __version__.

Examples:
  python scripts/test_update.py
  python scripts/test_update.py --as-version 1.0.0
  python scripts/test_update.py --as-version 1.0.0 --download
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

# Project root on sys.path when run as `python scripts/test_update.py`
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PyQt6.QtWidgets import QApplication

from src import __version__
from src.backend.updater import (
    check_for_update,
    download_update,
    normalize_update_check_url,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test Nudge update check (and optional download).",
    )
    parser.add_argument(
        "--as-version",
        metavar="VER",
        default=__version__,
        help=f"Pretend the app is this version (default: installed {__version__})",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Override update check URL (default: Pingwyd/Nudge GitHub API)",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Also download the release asset to %%TEMP%%\\Nudge_update",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Network timeout in seconds (default: 15)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    app = QApplication([])

    check_url = normalize_update_check_url(args.url)
    print(f"Checking as version {args.as_version!r}")
    print(f"URL: {check_url}\n")

    result = check_for_update(
        args.as_version,
        check_url=check_url,
        timeout=args.timeout,
    )

    if result.error:
        print("CHECK FAILED")
        print(f"  error: {result.error}")
        return 1

    if not result.available:
        print("CHECK OK — already up to date")
        print(f"  current: {args.as_version}")
        return 0

    print("CHECK OK — update available")
    print(f"  latest:  {result.latest_version}")
    print(f"  kind:    {result.asset_kind or '(unknown)'}")
    print(f"  url:     {result.download_url}")

    if not args.download:
        print("\nAdd --download to fetch the asset.")
        return 0

    if not result.download_url:
        print("\nDOWNLOAD SKIPPED — no download URL")
        return 1

    dest_dir = Path(tempfile.gettempdir()) / "Nudge_update"
    print(f"\nDownloading to {dest_dir} ...")

    def _progress(done: int, total: int) -> None:
        if total > 0:
            pct = min(100, int(done * 100 / total))
            print(f"\r  {pct:3d}%  ({done:,} / {total:,} bytes)", end="", flush=True)
        else:
            print(f"\r  {done:,} bytes", end="", flush=True)

    path, err = download_update(
        result.download_url,
        dest_dir,
        result.latest_version,
        progress_callback=_progress,
        asset_kind=result.asset_kind,
    )
    print()

    if path is None:
        print("DOWNLOAD FAILED")
        print(f"  error: {err}")
        return 1

    size = path.stat().st_size
    print("DOWNLOAD OK")
    print(f"  path: {path}")
    print(f"  size: {size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
