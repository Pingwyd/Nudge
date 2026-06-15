"""
Empty test stubs for each fix in the decision log.

These become the acceptance checklist. Fill them in as fixes are implemented.
Each stub is skipped until the corresponding fix is ready for testing.
"""
import pytest


# ── Fix: Glass bleed-through on overlap ────────────────────────────────

@pytest.mark.skip(reason="Not implemented yet")
def test_glass_overlap_applies_solid_background():
    """When a dialog overlaps the main window, bg_frame should get glass_overlap_solid."""
    pass


@pytest.mark.skip(reason="Not implemented yet")
def test_glass_overlap_clears_on_separation():
    """When a dialog moves away from overlap, bg_frame should revert to normal glass."""
    pass


# ── Fix: focusOutEvent auto-dismiss ────────────────────────────────────

@pytest.mark.skip(reason="Not implemented yet")
def test_themed_dialog_dismisses_on_focus_out():
    """ThemedMessageDialog should auto-accept when focus leaves."""
    pass


@pytest.mark.skip(reason="Not implemented yet")
def test_question_dialog_does_not_auto_dismiss():
    """Question-type dialogs should NOT auto-dismiss on focus out."""
    pass


# ── Fix: Context menu theme consistency ────────────────────────────────

@pytest.mark.skip(reason="Not implemented yet")
def test_context_menu_applies_theme_styling():
    """All QMenu instances should pick up the current theme's menu_bg, text, border."""
    pass


# ── Fix: Settings sidebar clipping ─────────────────────────────────────

@pytest.mark.skip(reason="Not implemented yet")
def test_settings_sidebar_text_fits():
    """Sidebar button text should not be clipped at default settings window size."""
    pass


@pytest.mark.skip(reason="Not implemented yet")
def test_settings_checkbox_text_fits():
    """General tab checkbox labels should not be clipped."""
    pass


# ── Fix: Update download retry + PowerShell fallback ───────────────────

@pytest.mark.skip(reason="Not implemented yet")
def test_download_retries_once_before_fallback():
    """download_update should retry SSL once before trying PowerShell."""
    pass


@pytest.mark.skip(reason="Not implemented yet")
def test_download_returns_error_message():
    """download_update should return (None, error_string) on failure, not just None."""
    pass


# ── Fix: Frozen check prevents dev-mode install ────────────────────────

@pytest.mark.skip(reason="Not implemented yet")
def test_perform_update_skips_when_not_frozen():
    """perform_update should return True without installing when sys.frozen is False."""
    pass


# ── Fix: Window size persistence ───────────────────────────────────────

@pytest.mark.skip(reason="Not implemented yet")
def test_history_window_size_persists():
    """History dialog size should be saved to state_manager on resize."""
    pass


@pytest.mark.skip(reason="Not implemented yet")
def test_settings_window_size_persists():
    """Settings dialog size should be saved to state_manager on resize."""
    pass


# ── Fix: Resize cursor hit zone ────────────────────────────────────────

@pytest.mark.skip(reason="Not implemented yet")
def test_resize_margin_is_adequate():
    """RESIZE_MARGIN should be >= 12 for comfortable edge hitting."""
    pass
