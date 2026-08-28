"""Manages side-dialog lifecycle and placement."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PyQt6.QtCore import QRect
    from PyQt6.QtWidgets import QDialog, QWidget

logger = logging.getLogger(__name__)


class DialogManager:
    """Tracks open side dialogs and positions them to avoid overlapping."""

    def __init__(self, main_window: Any):
        self._mw = main_window
        self._active_side_dialog: QWidget | None = None
        self._history_dialog: QWidget | None = None
        self._settings_dialog: QWidget | None = None
        self._export_dialog: QWidget | None = None
        self._reminders_dialog: QWidget | None = None

    def run_side_dialog(self, dialog: QDialog) -> None:
        """Show a non-modal side panel and track it for export avoidance."""
        self._active_side_dialog = dialog
        self._mw_show_dim()
        dialog.finished.connect(lambda r, d=dialog: self._on_side_dialog_closed(d))
        dialog.show()

    def _mw_show_dim(self) -> None:
        overlay = getattr(self._mw, "_dim_overlay", None)
        if overlay is not None:
            overlay.show_dim()

    def _mw_hide_dim(self) -> None:
        overlay = getattr(self._mw, "_dim_overlay", None)
        if overlay is not None:
            overlay.hide_dim()

    def _on_side_dialog_closed(self, dialog: QDialog) -> None:
        if self._active_side_dialog is dialog:
            self._active_side_dialog = None
        if self._history_dialog is dialog:
            self._history_dialog = None
        if self._settings_dialog is dialog:
            self._settings_dialog = None
        if self._export_dialog is dialog:
            self._export_dialog = None
        if self._reminders_dialog is dialog:
            self._reminders_dialog = None
        self._mw_hide_dim()
        dialog.deleteLater()

    def window_rects_to_avoid(self, extra: QDialog | None = None) -> list:
        """Rects export must not overlap: main window plus any open side panel."""
        rects = [self._mw.frameGeometry()]
        if extra is not None:
            rects.append(extra.frameGeometry())
        elif self._active_side_dialog is not None:
            rects.append(self._active_side_dialog.frameGeometry())
        return rects

    def center_on_parent(self, dialog: QDialog) -> None:
        """Center a dialog on the main window (not the monitor)."""
        parent = self._mw
        if dialog.width() <= 0 or dialog.height() <= 0:
            dialog.adjustSize()
        pg = parent.frameGeometry()
        x = pg.x() + (pg.width() - dialog.width()) // 2
        y = pg.y() + (pg.height() - dialog.height()) // 2
        # Keep mostly on-screen while staying anchored to the app window
        screen = parent.screen()
        if screen is not None:
            avail = screen.availableGeometry()
            x = max(avail.left(), min(x, avail.right() - dialog.width()))
            y = max(avail.top(), min(y, avail.bottom() - dialog.height()))
        dialog.move(x, y)

    def place_dialog_near_geometry(
        self,
        dialog: QDialog,
        ref_geom,
        *,
        y_offset: int = 0,
        prefer_right: bool = False,
    ) -> None:
        """Place a dialog beside a reference rect, clamped to the screen work area (H6)."""
        from PyQt6.QtCore import QRect

        screen = self._mw.screen()
        available = screen.availableGeometry() if screen else ref_geom

        if dialog.width() <= 0 or dialog.height() <= 0:
            dialog.adjustSize()

        gap = 15
        dialog_w = dialog.width()
        dialog_h = dialog.height()
        left_x = ref_geom.left() - dialog_w - gap
        right_x = ref_geom.right() + gap

        fits_left = left_x >= available.left()
        fits_right = right_x + dialog_w <= available.right()

        if prefer_right:
            if fits_right:
                target_x = right_x
            elif fits_left:
                target_x = left_x
            else:
                target_x = max(
                    available.left(),
                    min(ref_geom.left(), available.right() - dialog_w),
                )
        else:
            if fits_left:
                target_x = left_x
            elif fits_right:
                target_x = right_x
            else:
                target_x = max(
                    available.left(),
                    available.right() - dialog_w,
                )

        target_y = max(
            available.top(),
            min(ref_geom.top() + y_offset, available.bottom() - dialog_h),
        )
        dialog.move(target_x, target_y)

    def place_dialog_near_main_window(self, dialog: QDialog, *, y_offset: int = 0) -> None:
        """Place a dialog beside the main window, clamped to the screen work area (H6)."""
        self.place_dialog_near_geometry(dialog, self._mw.geometry(), y_offset=y_offset)

    def place_dialog_avoiding_rects(
        self,
        dialog: QDialog,
        avoid_rects: list,
        *,
        y_offset: int = 0,
        gap: int = 15,
    ) -> None:
        """Place dialog beside app windows without overlapping them (H6b)."""
        from PyQt6.QtCore import QRect

        if not avoid_rects:
            self.place_dialog_near_main_window(dialog, y_offset=y_offset)
            return

        screen = self._mw.screen()
        available = screen.availableGeometry() if screen else avoid_rects[0]

        if dialog.width() <= 0 or dialog.height() <= 0:
            dialog.adjustSize()

        dialog_w = dialog.width()
        dialog_h = dialog.height()

        union = avoid_rects[0]
        for rect in avoid_rects[1:]:
            union = union.united(rect)

        candidates = [
            (union.right() + gap, union.top() + y_offset),
            (union.left() - gap - dialog_w, union.top() + y_offset),
            (union.right() + gap, union.bottom() - dialog_h),
            (union.left() - gap - dialog_w, union.bottom() - dialog_h),
            (union.left(), union.top() - gap - dialog_h),
            (union.left(), union.bottom() + gap),
        ]

        def overlaps(x: int, y: int) -> bool:
            dlg_rect = QRect(x, y, dialog_w, dialog_h)
            for rect in avoid_rects:
                padded = rect.adjusted(-gap, -gap, gap, gap)
                if dlg_rect.intersects(padded):
                    return True
            return False

        for x, y in candidates:
            x = max(available.left(), min(x, available.right() - dialog_w))
            y = max(available.top(), min(y, available.bottom() - dialog_h))
            if not overlaps(x, y):
                dialog.move(x, y)
                return

        self.place_dialog_near_geometry(dialog, union, y_offset=y_offset, prefer_right=True)
