"""
Window z-order modes for the main widget (Stage 5).

Always on Top (WindowStaysOnTopHint) and Pin to Desktop (WindowStaysOnBottomHint)
are mutually exclusive at the OS level — never apply both.
"""

from PyQt6.QtCore import Qt


def compose_main_window_flags(pinned_to_desktop: bool, always_on_top: bool) -> Qt.WindowType:
    """
    Build frameless window flags with at most one layer hint.

    Pin to desktop wins if both are requested (callers should prevent that in UI).
    """
    flags = Qt.WindowType.FramelessWindowHint
    if pinned_to_desktop:
        return flags | Qt.WindowType.WindowStaysOnBottomHint
    if always_on_top:
        return flags | Qt.WindowType.WindowStaysOnTopHint
    return flags


def reconcile_layer_settings(state: dict) -> dict:
    """
    Ensure pinnedToDesktop and alwaysOnTop are not both True.
    Returns the same dict (mutated) for chaining.
    """
    if state.get("pinnedToDesktop") and state.get("alwaysOnTop"):
        # Prefer desktop pin if both were set (e.g. corrupted config).
        state["alwaysOnTop"] = False
    return state
