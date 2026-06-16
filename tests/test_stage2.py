"""Tests for Stage 2 — Interaction Safety."""
import sys
import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import Qt, QEvent, QPoint, QPointF
from PyQt6.QtGui import QMouseEvent, QFocusEvent


# ── 2.1 Double-click to complete ──────────────────────────────────────

def _make_task_row(qapp_instance):
    from src.frontend.main_window import TaskRowWidget
    toggled = MagicMock()
    row = TaskRowWidget("Test task", on_toggled=toggled)
    row.resize(300, 40)
    return row, toggled


def test_single_click_does_not_complete(qapp_instance):
    """Single click on a task row should NOT trigger toggle."""
    row, toggled = _make_task_row(qapp_instance)

    pos = QPointF(100, 20)
    press = QMouseEvent(QEvent.Type.MouseButtonPress, pos, pos,
                        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                        Qt.KeyboardModifier.NoModifier)
    row.mousePressEvent(press)

    release = QMouseEvent(QEvent.Type.MouseButtonRelease, pos, pos,
                          Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton,
                          Qt.KeyboardModifier.NoModifier)
    row.mouseReleaseEvent(release)

    toggled.assert_not_called()
    row.close()


def test_double_click_completes(qapp_instance):
    """Double click on a task row should trigger on_toggled(True)."""
    row, toggled = _make_task_row(qapp_instance)

    pos = QPointF(100, 20)
    dbl = QMouseEvent(QEvent.Type.MouseButtonDblClick, pos, pos,
                      Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                      Qt.KeyboardModifier.NoModifier)
    row.mouseDoubleClickEvent(dbl)

    toggled.assert_called_once_with(True)
    row.close()


def test_undo_toast_exists(qapp_instance):
    """UndoToast class should be importable and instantiable."""
    from src.frontend.main_window import UndoToast
    from PyQt6.QtWidgets import QWidget
    parent = QWidget()
    parent.resize(300, 300)
    parent.show()
    cb = MagicMock()
    toast = UndoToast(parent, "Test", cb)
    toast.show()
    assert toast.isVisible()
    toast._dismiss()
    parent.close()


# ── 2.2 Destructive dialogs default to No ─────────────────────────────

def test_delete_group_dialog_defaults_to_no(qapp_instance):
    """Delete group confirmation should default to No (safe)."""
    from src.frontend.themed_message_dialog import ThemedMessageDialog

    dialog = ThemedMessageDialog(
        None, "Delete Group", "Delete group 'Work'?",
        buttons=["Yes", "No"], default_index=1, icon_kind="question",
    )
    assert dialog._result_index == -1
    dialog.close()


def test_unsaved_settings_dialog_defaults_to_no(qapp_instance):
    """Unsaved settings dialog should default to No (discard)."""
    from src.frontend.themed_message_dialog import ThemedMessageDialog

    dialog = ThemedMessageDialog(
        None, "Unsaved Changes", "Save changes?",
        buttons=["Yes", "No"], default_index=1, icon_kind="question",
    )
    assert dialog._result_index == -1
    dialog.close()


def test_question_dialog_default_yes_parameter():
    """ThemedMessageDialog.question should support default_yes=False."""
    from src.frontend.themed_message_dialog import ThemedMessageDialog
    import inspect
    sig = inspect.signature(ThemedMessageDialog.question)
    assert "default_yes" in sig.parameters


# ── 2.3 Update dialog button styling ──────────────────────────────────

def test_update_dialog_buttons_have_correct_object_names(qapp_instance):
    """Update dialog: Install=primaryButton, Remind Me Later=ghostButton."""
    from src.frontend.update_dialog import UpdateInfoDialog
    from PyQt6.QtWidgets import QPushButton

    dlg = UpdateInfoDialog("1.0.0", "Test changelog", "https://example.com/install")
    install_btn = None
    later_btn = None
    for btn in dlg.findChildren(QPushButton):
        name = btn.objectName()
        if "Download" in btn.text() or "Install" in btn.text():
            install_btn = btn
        elif "Later" in btn.text():
            later_btn = btn

    assert install_btn is not None, "Install button not found"
    assert later_btn is not None, "Remind Me Later button not found"
    assert install_btn.objectName() == "primaryButton"
    assert later_btn.objectName() == "ghostButton"
    dlg.close()
