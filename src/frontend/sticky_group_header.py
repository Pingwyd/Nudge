"""Sticky group header selection (viewport geometry, no Qt dependency)."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

# (is_hidden, header_top, header_height, section_bottom) in viewport coordinates
StickyCandidate = Tuple[bool, int, int, int]


def pick_sticky_section_index(candidates: Sequence[StickyCandidate]) -> Optional[int]:
    """Pick the group whose header is crossing the top edge of the scroll viewport.

    Among sections whose header has scrolled above y=0 but the section still extends
    below the pin bar, choose the one with the largest header_top (closest to 0).
    """
    best_index: Optional[int] = None
    best_header_top: Optional[int] = None

    for index, (hidden, header_top, header_height, section_bottom) in enumerate(candidates):
        if hidden:
            continue
        if header_top >= 0:
            continue
        if section_bottom <= header_height:
            continue
        if best_header_top is None or header_top > best_header_top:
            best_header_top = header_top
            best_index = index

    return best_index
