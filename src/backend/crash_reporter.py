"""Capture unhandled exceptions, log locally, and show a report dialog."""

from __future__ import annotations

import os
import platform
import sys
import textwrap
import traceback
from datetime import datetime
from pathlib import Path

from src import __version__

CRASH_LOG_DIR = Path(os.environ.get("TEMP", ".")) / "Nudge"
CRASH_LOG_PATH = CRASH_LOG_DIR / "crash.log"


def _format_traceback(exc_type, exc_value, exc_tb) -> str:
    lines = [
        "=" * 60,
        f"Nudge Crash Report",
        "=" * 60,
        f"Timestamp:  {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"Version:    {__version__}",
        f"Python:     {sys.version}",
        f"Platform:   {platform.platform()}",
        f"Machine:    {platform.machine()}",
        "-" * 60,
        "",
    ]
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    lines.extend(tb_lines)
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def write_crash_log(exc_type, exc_value, exc_tb) -> Path:
    CRASH_LOG_DIR.mkdir(parents=True, exist_ok=True)
    report = _format_traceback(exc_type, exc_value, exc_tb)
    with open(CRASH_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(report)
        f.write("\n")
    return CRASH_LOG_PATH


def build_mailto_body(exc_type, exc_value, exc_tb) -> str:
    """Return a URL-escaped body string for a mailto: link."""
    body = _format_traceback(exc_type, exc_value, exc_tb)
    # Simple percent-encoding for mailto body
    encoded = (
        body
        .replace("%", "%25")
        .replace("\n", "%0A")
        .replace("&", "%26")
        .replace("?", "%3F")
        .replace("=", "%3D")
    )
    return encoded
