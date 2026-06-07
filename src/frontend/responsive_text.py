"""
Responsive wrapping text for task/history rows (Stage 3).

Keeps QLabel word-wrap in sync with row width as the main window or dialogs resize.
"""

from __future__ import annotations

from typing import Iterable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics, QTextOption
from PyQt6.QtWidgets import QLabel, QLineEdit, QSizePolicy, QStackedWidget, QWidget

# Avoid a single ultra-narrow text column when the window is at minimum width.
MIN_TEXT_COLUMN_WIDTH = 120


def configure_wrapping_label(label: QLabel) -> None:
    """QLabel that grows in height as wrapped lines increase (incl. unbroken long strings)."""
    label.setWordWrap(True)
    if hasattr(label, "setWordWrapMode"):
        label.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)


def apply_wrapped_text_width(label: QLabel, available_width: int) -> None:
    """Set width constraints so wrap reflows; prefer at least MIN_TEXT_COLUMN_WIDTH when possible."""
    width = max(1, available_width)
    label.setMaximumWidth(width)
    label.setMinimumWidth(min(width, MIN_TEXT_COLUMN_WIDTH))
    label.adjustSize()


def apply_editor_field_width(editor: QLineEdit, available_width: int) -> None:
    """Single-line editor: cap width only; height is fixed separately (Stage 4)."""
    width = max(1, available_width)
    editor.setMaximumWidth(width)
    editor.setMinimumWidth(0)


def fix_single_line_editor_height(editor: QLineEdit, vertical_padding: int = 14) -> None:
    """Keep edit rows compact — do not let QLineEdit inherit stack/list stretch height."""
    metrics = QFontMetrics(editor.font())
    editor.setFixedHeight(metrics.height() + vertical_padding)


def label_content_height(label: QLabel, column_width: int) -> int:
    """Estimate wrapped label height for the current column width."""
    metrics = QFontMetrics(label.font())
    wrap_flags = int(Qt.TextFlag.TextWordWrap)
    if hasattr(Qt.TextFlag, "TextWrapAnywhere"):
        wrap_flags |= int(Qt.TextFlag.TextWrapAnywhere)
    bounds = metrics.boundingRect(
        0,
        0,
        max(1, column_width),
        10000,
        wrap_flags,
        label.text(),
    )
    return bounds.height() + 4


def sync_stacked_page_height(stack: QStackedWidget, content_height: int) -> None:
    """Pin stack height to the active page so the hidden page cannot inflate the row."""
    stack.setFixedHeight(max(1, content_height))


def available_text_width(host: QWidget, reserved: Iterable[QWidget]) -> int:
    """Pixels left for the text column after margins, spacing, and sibling widgets."""
    layout = host.layout()
    if layout is None:
        return max(1, host.width())

    available = host.width()
    margins = layout.contentsMargins()
    available -= margins.left() + margins.right()

    reserved_set = set(reserved)
    widget_count = 0
    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item is None or item.widget() is None:
            continue
        widget_count += 1
        widget = item.widget()
        if widget in reserved_set:
            w = widget.width() or widget.sizeHint().width()
            available -= w

    if widget_count > 1:
        available -= layout.spacing() * (widget_count - 1)

    return max(MIN_TEXT_COLUMN_WIDTH, available)


class ResponsiveTextRowHelper:
    """Sync a wrapping label (and optional editor) to the host row width."""

    def __init__(
        self,
        host: QWidget,
        label: QLabel,
        reserved_widgets: Iterable[QWidget],
        editor: Optional[QWidget] = None,
    ):
        self.host = host
        self.label = label
        self.reserved_widgets = tuple(reserved_widgets)
        self.editor = editor
        configure_wrapping_label(label)

    def sync_layout(self) -> None:
        width = available_text_width(self.host, self.reserved_widgets)
        apply_wrapped_text_width(self.label, width)
        if self.editor is not None:
            apply_editor_field_width(self.editor, width)
            fix_single_line_editor_height(self.editor)
