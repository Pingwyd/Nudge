"""Pytest configuration for Nudge tests."""
import os
import sys

# Ensure offscreen Qt platform for headless tests
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


@pytest.fixture(scope="session")
def qapp_instance():
    """Shared QApplication for the test session."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
