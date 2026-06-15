"""Tests for Stage 1 fixes."""
import pytest
from unittest.mock import patch, MagicMock


# ── 1.1 Feedback send handler ─────────────────────────────────────────

def test_feedback_send_handler_opens_gmail(qapp_instance):
    """Feedback dialog _send_feedback should call open_url with a Gmail URI."""
    from src.frontend.feedback_dialog import FeedbackDialog

    dlg = FeedbackDialog(None, "test snapshot")
    dlg.input_edit.setPlainText("Test feedback")

    with patch("src.os_layer.platform_utils.open_url", return_value=True) as mock_open:
        with patch("src.frontend.feedback_dialog.QApplication.clipboard") as mock_clip:
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
