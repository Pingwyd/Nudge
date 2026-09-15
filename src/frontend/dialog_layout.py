"""Shared margins, titles, and footer rows for glass-panel dialogs."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.constants import (
    DIALOG_BTN_HEIGHT,
    DIALOG_BTN_MIN_WIDTH,
    DIALOG_CONTENT_MARGINS,
    DIALOG_FOOTER_GAP,
    DIALOG_SECTION_SPACING,
    SPACING_MD,
)

DialogButtonRole = str  # "ghost" | "primary" | "danger"
DialogButtonSpec = tuple[str, DialogButtonRole, Callable[[], None]]


def apply_dialog_content_layout(layout: QVBoxLayout) -> None:
    layout.setContentsMargins(*DIALOG_CONTENT_MARGINS)
    layout.setSpacing(DIALOG_SECTION_SPACING)


def make_dialog_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("dialogTitle")
    return label


def _object_name_for_role(role: DialogButtonRole) -> str:
    if role == "primary":
        return "primaryButton"
    if role == "danger":
        return "dangerButton"
    return "ghostButton"


def add_dialog_footer(
    parent_layout: QVBoxLayout,
    buttons: Sequence[DialogButtonSpec],
) -> list[QPushButton]:
    """Right-aligned footer row with standard dialog button sizing."""
    parent_layout.addSpacing(DIALOG_FOOTER_GAP)
    row = QHBoxLayout()
    row.setSpacing(SPACING_MD)
    row.addStretch(1)
    created: list[QPushButton] = []
    for label, role, slot in buttons:
        btn = QPushButton(label)
        btn.setObjectName(_object_name_for_role(role))
        btn.setFixedHeight(DIALOG_BTN_HEIGHT)
        btn.setMinimumWidth(DIALOG_BTN_MIN_WIDTH)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(slot)
        if role == "primary":
            btn.setDefault(True)
        row.addWidget(btn)
        created.append(btn)
    parent_layout.addLayout(row)
    return created
