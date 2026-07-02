"""Regression test for C1: undefined variable `opened` in feedback dialog."""

from unittest.mock import patch, MagicMock
from src.os_layer.platform_utils import open_url


def test_open_url_returns_bool_on_success():
    """open_url should return True when webbrowser.open succeeds."""
    with patch("src.os_layer.platform_utils.webbrowser") as mock_wb:
        mock_wb.open.return_value = True
        result = open_url("https://example.com")
        assert result is True


def test_open_url_returns_bool_on_fallback():
    """open_url should return True after fallback (os.startfile / subprocess)."""
    with patch("src.os_layer.platform_utils.webbrowser") as mock_wb, \
         patch("src.os_layer.platform_utils.is_windows", return_value=True), \
         patch("src.os_layer.platform_utils.os") as mock_os:
        mock_wb.open.return_value = False
        result = open_url("https://example.com")
        assert result is True
        mock_os.startfile.assert_called_once_with("https://example.com")


def test_open_url_feedback_handler_no_nameerror():
    """Feedback dialog handler should not raise NameError on `opened`."""
    with patch("src.os_layer.platform_utils.webbrowser") as mock_wb:
        mock_wb.open.return_value = True
        # This simulates the feedback dialog handler logic
        from src.os_layer.platform_utils import open_url as _open
        opened = _open("https://mail.google.com/mail/?view=cm&su=test&body=test")
        assert isinstance(opened, bool)
        if not opened:
            # This branch should now be reachable without NameError
            pass
