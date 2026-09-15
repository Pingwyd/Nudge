"""Unit tests for sticky group header selection geometry."""

from src.frontend.sticky_group_header import pick_sticky_section_index


def test_pick_none_when_all_headers_below_fold():
    # header_top >= 0 for all
    candidates = [
        (False, 10, 32, 200),
        (False, 80, 32, 400),
    ]
    assert pick_sticky_section_index(candidates) is None


def test_pick_section_crossing_top_edge():
    candidates = [
        (False, -50, 32, 100),  # scrolled away mostly
        (False, -5, 32, 300),   # current fold — max header_top among negatives
        (False, 40, 32, 500),
    ]
    assert pick_sticky_section_index(candidates) == 1


def test_pick_max_header_top_among_matches():
    candidates = [
        (False, -20, 32, 250),
        (False, -8, 32, 180),
        (False, -15, 32, 400),
    ]
    assert pick_sticky_section_index(candidates) == 1


def test_skip_hidden_and_fully_scrolled():
    candidates = [
        (True, -5, 32, 200),   # hidden
        (False, -10, 32, 20),  # section bottom above pin bar
        (False, -3, 32, 150),
    ]
    assert pick_sticky_section_index(candidates) == 2
