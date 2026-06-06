"""
Frameless window chrome: edge/corner resize and title-bar drag for PyQt6.

Used with Qt.WindowType.FramelessWindowHint — the OS does not provide resize
handles, so we detect pointer position near edges and adjust geometry manually.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QCursor

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

from src.backend.window_geometry import (
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
)

RESIZE_MARGIN = 9
TITLE_BAR_DRAG_HEIGHT = 44


class ResizeEdges:
  NONE = 0
  LEFT = 1
  RIGHT = 2
  TOP = 4
  BOTTOM = 8


def hit_test_resize_edges(local_pos: QPoint, width: int, height: int, margin: int = RESIZE_MARGIN) -> int:
  """Return a bitmask of ResizeEdges for pointer position inside the window."""
  x, y = local_pos.x(), local_pos.y()
  edges = ResizeEdges.NONE
  if x <= margin:
    edges |= ResizeEdges.LEFT
  if x >= width - margin:
    edges |= ResizeEdges.RIGHT
  if y <= margin:
    edges |= ResizeEdges.TOP
  if y >= height - margin:
    edges |= ResizeEdges.BOTTOM
  return edges


def cursor_for_resize_edges(edges: int) -> Qt.CursorShape:
  if edges in (ResizeEdges.LEFT | ResizeEdges.RIGHT, ResizeEdges.LEFT, ResizeEdges.RIGHT):
    return Qt.CursorShape.SizeHorCursor
  if edges in (ResizeEdges.TOP | ResizeEdges.BOTTOM, ResizeEdges.TOP, ResizeEdges.BOTTOM):
    return Qt.CursorShape.SizeVerCursor
  if edges in (
    ResizeEdges.TOP | ResizeEdges.LEFT,
    ResizeEdges.BOTTOM | ResizeEdges.RIGHT,
  ):
    return Qt.CursorShape.SizeFDiagCursor
  if edges in (
    ResizeEdges.TOP | ResizeEdges.RIGHT,
    ResizeEdges.BOTTOM | ResizeEdges.LEFT,
  ):
    return Qt.CursorShape.SizeBDiagCursor
  return Qt.CursorShape.ArrowCursor


def is_title_bar_drag_zone(local_pos: QPoint, edges: int) -> bool:
  """Allow window move only from the top chrome, not from resize grips."""
  if edges != ResizeEdges.NONE:
    return False
  return local_pos.y() <= TITLE_BAR_DRAG_HEIGHT


class FramelessChromeController:
  """Handles resize + title-bar drag for a frameless top-level window."""

  def __init__(
    self,
    window: QWidget,
    min_width: int = MIN_WINDOW_WIDTH,
    min_height: int = MIN_WINDOW_HEIGHT,
    resize_margin: int = RESIZE_MARGIN,
  ):
    self.window = window
    self.min_width = min_width
    self.min_height = min_height
    self.resize_margin = resize_margin
    self._resize_edges: int = ResizeEdges.NONE
    self._resize_origin_global: Optional[QPoint] = None
    self._resize_start_geom: Optional[QRect] = None
    self._dragging = False
    self._drag_offset: Optional[QPoint] = None

  @property
  def is_resizing(self) -> bool:
    return self._resize_edges != ResizeEdges.NONE

  @property
  def is_dragging(self) -> bool:
    return self._dragging

  def update_hover_cursor(self, local_pos: QPoint) -> None:
    if self.is_resizing or self._dragging:
      return
    edges = hit_test_resize_edges(
      local_pos, self.window.width(), self.window.height(), self.resize_margin
    )
    self.window.setCursor(QCursor(cursor_for_resize_edges(edges)))

  def handle_mouse_press(self, global_pos: QPoint, local_pos: QPoint, position_locked: bool) -> bool:
    """Return True if the event was consumed (resize or drag started)."""
    edges = hit_test_resize_edges(
      local_pos, self.window.width(), self.window.height(), self.resize_margin
    )
    if edges != ResizeEdges.NONE:
      self._resize_edges = edges
      self._resize_origin_global = global_pos
      self._resize_start_geom = self.window.frameGeometry()
      self.window.setCursor(QCursor(cursor_for_resize_edges(edges)))
      return True

    if not position_locked and is_title_bar_drag_zone(local_pos, edges):
      self._dragging = True
      self._drag_offset = global_pos - self.window.frameGeometry().topLeft()
      self.window.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
      return True

    return False

  def handle_mouse_move(self, global_pos: QPoint, local_pos: QPoint) -> bool:
    if self.is_resizing and self._resize_origin_global is not None and self._resize_start_geom is not None:
      self._apply_resize(global_pos)
      return True

    if self._dragging and self._drag_offset is not None:
      self.window.move(global_pos - self._drag_offset)
      return True

    self.update_hover_cursor(local_pos)
    return False

  def handle_mouse_release(self) -> bool:
    was_active = self.is_resizing or self._dragging
    self._resize_edges = ResizeEdges.NONE
    self._resize_origin_global = None
    self._resize_start_geom = None
    self._dragging = False
    self._drag_offset = None
    self.window.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
    return was_active

  def _apply_resize(self, global_pos: QPoint) -> None:
    assert self._resize_origin_global is not None
    assert self._resize_start_geom is not None

    delta = global_pos - self._resize_origin_global
    rect = QRect(self._resize_start_geom)
    edges = self._resize_edges

    if edges & ResizeEdges.LEFT:
      new_left = rect.left() + delta.x()
      max_left = rect.right() - self.min_width + 1
      rect.setLeft(min(new_left, max_left))
    if edges & ResizeEdges.RIGHT:
      new_width = rect.width() + delta.x()
      rect.setWidth(max(self.min_width, new_width))
    if edges & ResizeEdges.TOP:
      new_top = rect.top() + delta.y()
      max_top = rect.bottom() - self.min_height + 1
      rect.setTop(min(new_top, max_top))
    if edges & ResizeEdges.BOTTOM:
      new_height = rect.height() + delta.y()
      rect.setHeight(max(self.min_height, new_height))

    self.window.setGeometry(rect)
