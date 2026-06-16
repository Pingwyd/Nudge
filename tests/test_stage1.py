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


# ── 1.4 Period-Split Parser ───────────────────────────────────────────

def test_period_split_sentences():
    """Period-space splits into separate tasks."""
    from src.backend.input_parser import InputParser
    tasks = InputParser.parse_input("Buy eggs. Get milk.")
    assert len(tasks) == 2
    assert tasks[0]["text"] == "Buy eggs"
    assert tasks[1]["text"] == "Get milk"


def test_period_split_abbreviation():
    """Abbreviation like Dr. should not split."""
    from src.backend.input_parser import InputParser
    tasks = InputParser.parse_input("Dr. Smith buys eggs.")
    assert len(tasks) == 1
    assert tasks[0]["text"] == "Dr. Smith buys eggs"


def test_period_split_ellipsis():
    """Ellipsis (...) should not split."""
    from src.backend.input_parser import InputParser
    tasks = InputParser.parse_input("Wait... then go home.")
    assert len(tasks) == 1
    assert tasks[0]["text"] == "Wait... then go home"


def test_period_split_decimal():
    """Decimal like 3.14 should not split."""
    from src.backend.input_parser import InputParser
    tasks = InputParser.parse_input("Value is 3.14.")
    assert len(tasks) == 1
    assert tasks[0]["text"] == "Value is 3.14"


def test_period_split_empty():
    """Empty input returns empty list."""
    from src.backend.input_parser import InputParser
    assert InputParser.parse_input("") == []
    assert InputParser.parse_input("   ") == []


def test_period_split_single():
    """Single sentence without period."""
    from src.backend.input_parser import InputParser
    tasks = InputParser.parse_input("Buy eggs")
    assert len(tasks) == 1
    assert tasks[0]["text"] == "Buy eggs"


# ── 8.1 Feedback Character Count Display ──────────────────────────────

def test_char_count_format(qapp_instance):
    """Character counter should display 'N / 1000' format."""
    from src.frontend.feedback_dialog import FeedbackDialog

    dlg = FeedbackDialog(None, "snapshot")
    dlg.input_edit.setPlainText("Hello")
    assert dlg._char_count.text() == "5 / 1000"
    dlg.close()


def test_char_count_zero(qapp_instance):
    """Character counter starts at '0 / 1000'."""
    from src.frontend.feedback_dialog import FeedbackDialog

    dlg = FeedbackDialog(None, "snapshot")
    assert dlg._char_count.text() == "0 / 1000"
    dlg.close()


def test_char_count_at_limit(qapp_instance):
    """Counter uses danger color when at 1000 characters."""
    from src.frontend.feedback_dialog import FeedbackDialog
    from src.constants import FEEDBACK_MAX_CHARS

    dlg = FeedbackDialog(None, "snapshot")
    dlg.input_edit.setPlainText("A" * FEEDBACK_MAX_CHARS)
    text = dlg._char_count.text()
    assert text == f"{FEEDBACK_MAX_CHARS} / {FEEDBACK_MAX_CHARS}"
    # Check danger styling is applied (font-weight: bold)
    style = dlg._char_count.styleSheet()
    assert "bold" in style
    dlg.close()


def test_char_count_below_limit_normal_style(qapp_instance):
    """Counter uses normal muted style when below limit."""
    from src.frontend.feedback_dialog import FeedbackDialog

    dlg = FeedbackDialog(None, "snapshot")
    dlg.input_edit.setPlainText("Short")
    style = dlg._char_count.styleSheet()
    assert "bold" not in style
    assert "opacity" in style
    dlg.close()


def test_char_count_blocks_input_at_limit(qapp_instance):
    """Typing should be blocked when at character limit."""
    from src.frontend.feedback_dialog import FeedbackDialog
    from src.constants import FEEDBACK_MAX_CHARS
    from PyQt6.QtGui import QKeyEvent

    dlg = FeedbackDialog(None, "snapshot")
    dlg.input_edit.setPlainText("A" * FEEDBACK_MAX_CHARS)

    # Simulate typing 'x' via event filter — should be blocked
    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_X, Qt.KeyboardModifier.NoModifier, "x")
    dlg.eventFilter(dlg.input_edit, event)
    assert dlg.input_edit.toPlainText() == "A" * FEEDBACK_MAX_CHARS  # unchanged
    dlg.close()


def test_char_count_allows_backspace_at_limit(qapp_instance):
    """Backspace should work even when at character limit."""
    from src.frontend.feedback_dialog import FeedbackDialog
    from src.constants import FEEDBACK_MAX_CHARS
    from PyQt6.QtGui import QKeyEvent

    dlg = FeedbackDialog(None, "snapshot")
    dlg.input_edit.setPlainText("A" * FEEDBACK_MAX_CHARS)

    # Simulate backspace via event filter — should be allowed
    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
    accepted = dlg.eventFilter(dlg.input_edit, event)
    # eventFilter returns False = pass through to QTextEdit (not blocked)
    assert not accepted
    dlg.close()


def test_char_count_allows_delete_at_limit(qapp_instance):
    """Delete key should work even when at character limit."""
    from src.frontend.feedback_dialog import FeedbackDialog
    from src.constants import FEEDBACK_MAX_CHARS
    from PyQt6.QtGui import QKeyEvent

    dlg = FeedbackDialog(None, "snapshot")
    dlg.input_edit.setPlainText("A" * FEEDBACK_MAX_CHARS)

    # Simulate delete via event filter — should be allowed
    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier)
    accepted = dlg.eventFilter(dlg.input_edit, event)
    # eventFilter returns False = pass through to QTextEdit (not blocked)
    assert not accepted
    dlg.close()


def test_char_count_allows_shortcut_keys(qapp_instance):
    """Modifier-only keystrokes (Ctrl+C etc.) should pass through at limit."""
    from src.frontend.feedback_dialog import FeedbackDialog
    from src.constants import FEEDBACK_MAX_CHARS
    from PyQt6.QtGui import QKeyEvent

    dlg = FeedbackDialog(None, "snapshot")
    dlg.input_edit.setPlainText("A" * FEEDBACK_MAX_CHARS)

    # Simulate Ctrl+C — modifier-only, no text, should pass through
    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    accepted = dlg.eventFilter(dlg.input_edit, event)
    assert not accepted  # not blocked
    # Text should remain unchanged
    assert dlg.input_edit.toPlainText() == "A" * FEEDBACK_MAX_CHARS
    dlg.close()
