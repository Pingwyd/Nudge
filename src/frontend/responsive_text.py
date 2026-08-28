"""
Responsive wrapping text for task/history rows (Stage 3).

Keeps QLabel word-wrap in sync with row width as the main window or dialogs resize.
"""

from __future__ import annotations

from typing import Iterable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics, QTextOption
from PyQt6.QtWidgets import (QLabel, QLineEdit, QSizePolicy, QStackedWidget,
                             QWidget)


def min_text_column_width(available_width: int) -> int:
    return max(100, int(available_width * 0.4))


def configure_wrapping_label(label: QLabel) -> None:
    label.setWordWrap(True)
    if hasattr(label, "setWordWrapMode"):
        label.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
    label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)


def apply_wrapped_text_width(label: QLabel, available_width: int) -> None:
    width = max(1, available_width)
    label.setMaximumWidth(width)
    min_width = min(width, int(available_width * 0.4))
    min_width = max(min_width, min_text_column_width(available_width))
    label.setMinimumWidth(min_width)


def apply_editor_field_width(editor: QLineEdit, available_width: int) -> None:
    width = max(1, available_width)
    editor.setMaximumWidth(width)
    editor.setMinimumWidth(0)


def fix_single_line_editor_height(editor: QLineEdit, vertical_padding: int = 14) -> None:
    metrics = QFontMetrics(editor.font())
    editor.setFixedHeight(metrics.height() + vertical_padding)


def label_content_height(label: QLabel, column_width: int) -> int:
    """Return the height QLabel needs for *column_width* pixels of word-wrap."""
    hfw = label.heightForWidth(max(1, column_width))
    if hfw > 0:
        return hfw
    # Fallback for widgets that don't support height-for-width.
    metrics = QFontMetrics(label.font())
    wrap_flags = int(Qt.TextFlag.TextWordWrap)
    if hasattr(Qt.TextFlag, "TextWrapAnywhere"):
        wrap_flags |= int(Qt.TextFlag.TextWrapAnywhere)
    bounds = metrics.boundingRect(
        0, 0, max(1, column_width), 10000, wrap_flags, label.text(),
    )
    return bounds.height() + 4


def sync_stacked_page_height(stack: QStackedWidget, content_height: int) -> None:
    """Lock the stack to exactly *content_height* pixels.

    Using only setMinimumHeight leaves the stack free to grow to its
    sizeHint(), which for a word-wrapping QLabel is calculated at the
    label's *current* (possibly narrow) width — often far too tall.
    Setting both min and max forces the layout to use our calculated height.
    The next sync_text_layout (triggered by resizeEvent) updates it.
    """
    h = max(1, content_height)
    stack.setMinimumHeight(h)
    stack.setMaximumHeight(h)


def available_text_width(host: QWidget, reserved: Iterable[QWidget]) -> int:
    """Pixels left for the text column after margins, spacing, and sibling widgets.

    Only subtracts widgets in *reserved* — the text container itself (e.g.
    content_stack with stretch=1) must NOT be in this list, because its width
    is the *result* of the layout allocation, not a fixed deduction.
    """
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
            # Prefer sizeHint() — updated immediately by updateGeometry()/setFixedWidth().
            # widget.width() can be stale before the layout engine re-runs.
            hint_w = widget.sizeHint().width()
            w = hint_w if hint_w > 0 else (widget.width() or hint_w)
            available -= w
    if widget_count > 1:
        available -= layout.spacing() * (widget_count - 1)
    return max(min_text_column_width(available), available)


class ResponsiveTextRowHelper:
    """Sync a wrapping label (and optional editor) within a host layout."""

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
        self._content_stack: Optional[QWidget] = None
        self.editor = editor
        configure_wrapping_label(label)

    def set_content_stack(self, stack: QWidget) -> None:
        """Tell the helper which widget's actual width is the text area."""
        self._content_stack = stack

    def sync_layout(self) -> int:
        """Set label/editor max-width and return the calculated width (px)."""
        width = available_text_width(self.host, self.reserved_widgets)
        apply_wrapped_text_width(self.label, width)
        if self.editor is not None:
            apply_editor_field_width(self.editor, width)
            fix_single_line_editor_height(self.editor)
        return width
