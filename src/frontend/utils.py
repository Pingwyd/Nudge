"""Shared frontend utility functions."""

from PyQt6.QtWidgets import QLabel


def set_label_point_size(label, point_size, bold=False):
    font = label.font()
    font.setPointSize(point_size)
    font.setBold(bold)
    label.setFont(font)
