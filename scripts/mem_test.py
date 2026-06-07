"""Automated memory leak test."""
import gc
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def count_objects(cls):
    return sum(1 for obj in gc.get_objects() if isinstance(obj, cls))


def test_dialog_leak(dialog_cls, parent=None):
    before = count_objects(dialog_cls)
    for _ in range(10):
        dlg = dialog_cls(parent)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dlg.exec()
    gc.collect()
    after = count_objects(dialog_cls)
    leaked = after - before
    if leaked > 0:
        print(f"[LEAK] {dialog_cls.__name__}: {leaked} instances leaked")
    else:
        print(f"[OK] {dialog_cls.__name__}: no leak")
    return leaked


if __name__ == "__main__":
    app = QApplication(sys.argv)

    from src.frontend.whats_new_dialog import WhatsNewDialog
    test_dialog_leak(WhatsNewDialog, None)

    from src.frontend.support_dialog import SupportDialog
    test_dialog_leak(SupportDialog, None)

    from src.frontend.settings_dialog import SettingsDialog
    # SettingsDialog needs state_manager
    from unittest.mock import MagicMock
    mock_state = {
        "taskTextSize": 14,
        "theme": "dark",
        "enableAnimations": True,
        "groupsEnabled": True,
        "aotPinned": False,
        "autoStartEnabled": False,
        "reminderInterval": 30,
    }
    mock_mgr = MagicMock()
    mock_mgr.state = mock_state
    dlg = SettingsDialog(mock_mgr, None)
    dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    dlg.exec()

    print("All mem tests done.")
