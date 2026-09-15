"""Sticky group header selection (viewport geometry, no Qt dependency)."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

# (is_hidden, header_top, header_height, section_bottom) in viewport coordinates
StickyCandidate = Tuple[bool, int, int, int]


def pick_sticky_section_index(candidates: Sequence[StickyCandidate]) -> Optional[int]:
    """Pick the group whose header is crossing the top edge of the scroll viewport.

    Among sections whose header has scrolled above y=0 but still intersects the
    viewport top (or the section remains visible), choose the largest header_top
    (closest to 0).
    """
    best_index: Optional[int] = None
    best_header_top: Optional[int] = None

    for index, (hidden, header_top, header_height, section_bottom) in enumerate(candidates):
        if hidden:
            continue
        if header_top >= 0:
            continue
        if section_bottom <= 0:
            continue
        if header_top + header_height <= 0:
            continue
        if best_header_top is None or header_top > best_header_top:
            best_header_top = header_top
            best_index = index

    return best_index


def header_intersects_pin_band(
    header_top: int,
    header_height: int,
    pin_height: int,
) -> bool:
    """True if the header widget rect intersects viewport y in [0, pin_height)."""
    if pin_height <= 0 or header_height <= 0:
        return False
    header_bottom = header_top + header_height
    return header_top < pin_height and header_bottom > 0


def should_conceal_in_list_header(section_group_id: str, pinned_id: str | None) -> bool:
    """Only the pinned group's in-list header is concealed; peek rows stay visible."""
    return pinned_id is not None and section_group_id == pinned_id
