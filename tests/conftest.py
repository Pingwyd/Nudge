"""Pytest configuration for Nudge tests."""
import os
import sys

# Ensure offscreen Qt platform for headless tests
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
