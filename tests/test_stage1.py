"""Tests for Stage 1 fixes."""
import sys
import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtCore import Qt


# ── 1.1 Feedback send handler ─────────────────────────────────────────

def test_feedback_send_handler_opens_gmail(qapp_instance):
    """Feedback dialog _send_feedback should call open_url with a Gmail URI."""
    from src.frontend.feedback_dialog import FeedbackDialog

    dlg = FeedbackDialog(None, "test snapshot")
    dlg.input_edit.setPlainText("Test feedback")

    with patch("src.os_layer.platform_utils.open_url", return_value=True) as mock_open:
        with patch("src.frontend.feedback_dialog.QApplication.clipboard"):
            dlg._send_feedback()
            mock_open.assert_called_once()
            uri = mock_open.call_args[0][0]
            assert "mail.google.com" in uri
            assert "nudgefeedback" in uri
            assert "Test%20feedback" in uri

    dlg.close()


def test_feedback_send_handler_rejects_empty(qapp_instance):
    """Feedback dialog _send_feedback should not open Gmail if text is empty."""
    from src.frontend.feedback_dialog import FeedbackDialog

    dlg = FeedbackDialog(None, "test snapshot")
    dlg.input_edit.setPlainText("")

    with patch("src.os_layer.platform_utils.open_url") as mock_open:
        dlg._send_feedback()
        mock_open.assert_not_called()

    dlg.close()


# ── 1.2 Crash Dialog Styling ──────────────────────────────────────────

def _make_crash_dialog(qapp_instance):
    from src.frontend.crash_dialog import CrashDialog
    try:
        raise ValueError("test error")
    except ValueError:
        exc_type, exc_value, exc_tb = sys.exc_info()
    return CrashDialog(exc_type, exc_value, exc_tb)


def test_crash_dialog_has_glass_panel(qapp_instance):
    """CrashDialog should have a glassPanel frame."""
    dlg = _make_crash_dialog(qapp_instance)
    assert dlg.bg_frame is not None
    assert dlg.bg_frame.objectName() == "glassPanel"
    dlg.close()


def test_crash_dialog_is_frameless(qapp_instance):
    """CrashDialog should be frameless with translucent background."""
    dlg = _make_crash_dialog(qapp_instance)
    flags = dlg.windowFlags()
    assert Qt.WindowType.FramelessWindowHint & flags
    dlg.close()


# ── 1.3 focusOutEvent Auto-Accept ─────────────────────────────────────

def test_focusout_event_closes_not_accepts(qapp_instance):
    """focusOutEvent should close() the dialog, not accept()."""
    from src.frontend.themed_message_dialog import ThemedMessageDialog

    dlg = ThemedMessageDialog(None, "Info", "Test message", icon_kind="info")
    dlg.show()

    from PyQt6.QtGui import QFocusEvent
    from PyQt6.QtCore import Qt as Qt2
    focus_event = QFocusEvent(QFocusEvent.Type.FocusOut)
    dlg.focusOutEvent(focus_event)

    # close() sets result to Rejected (0), accept() would set Accepted (1)
    assert dlg.result() != 1
    dlg.close()
