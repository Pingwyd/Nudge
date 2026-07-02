"""Centralized logging configuration for Nudge."""
import logging
import sys

_CONFIGURED = False


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger once. Subsequent calls are no-ops."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
