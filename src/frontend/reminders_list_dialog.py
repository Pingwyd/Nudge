"""Reminders list side-panel dialog."""
from __future__ import annotations
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)

from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.theme import get_theme, _c
from src.frontend.utils import set_label_point_size
from src.constants import (
    DIALOG_PLACEMENT_GAP,
    FONT_SIZE_BODY,
    FONT_SIZE_LABEL_MD,
    FONT_SIZE_TITLE_MD,
    PRIORITY_DIVIDER_HEIGHT,
    REMINDER_OVERLAP_RADIUS,
    REMINDERS_LIST_CLOSE_BTN_SIZE,
    REMINDERS_LIST_EMPTY_STATE_SIZE,
    REMINDERS_LIST_FILLED_STATE_SIZE,
    REMINDERS_LIST_MAIN_LAYOUT_MARGINS,
    REMINDERS_LIST_MIN_HEIGHT,
    RADIUS_SMALL,
    SPACING_LG,
    SPACING_MD,
    SPACING_SM,
    TIMER_DIALOG_BTN_HEIGHT,
)

if TYPE_CHECKING:
    from src.frontend.dialog_context import DialogContext

logger = logging.getLogger(__name__)


class RemindersListDialog(GlassPanelDialog):
    """Shows all pending reminders with cancel capability."""

    def __init__(self, ctx: DialogContext, parent: QWidget | None = None):
        super().__init__(parent=parent, overlap_radius=REMINDER_OVERLAP_RADIUS, escape_action="close")
        self._ctx = ctx
        self._focus_cleanup = None
        self.setWindowTitle("Reminders")
        self._build_ui()

    def _build_ui(self) -> None:
        theme = get_theme(self._ctx.app_state.get("theme", "dark"))
        tc = _c(theme, "text")
        tmc = _c(theme, "text_muted")
        hover = _c(theme, "hover")
        hover_strong = _c(theme, "hover_strong")
        border_c = _c(theme, "border")
        input_bg = _c(theme, "input_bg")

        now_ts = datetime.now().timestamp()
        pending = []
        for cfg_dict in self._ctx.timer_manager.to_list():
            if cfg_dict.get("taskId") is None:
                continue
            if not cfg_dict.get("enabled", True):
                continue
            trigger_at = cfg_dict.get("nextTriggerAt", 0)
            if trigger_at <= now_ts:
                continue
            remaining = int(trigger_at - now_ts)
            hours, remainder = divmod(remaining, 3600)
            minutes, secs = divmod(remainder, 60)
            if hours > 0:
                time_str = f"{hours}h {minutes}m"
            elif minutes > 0:
                time_str = f"{minutes}m {secs}s"
            else:
                time_str = f"{secs}s"
            name = cfg_dict.get("name", "Task reminder")
            pending.append((cfg_dict, f"{name[:60]}  — {time_str}"))

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*REMINDERS_LIST_MAIN_LAYOUT_MARGINS)
        layout.setSpacing(SPACING_LG)

        header = QHBoxLayout()
        header.setSpacing(SPACING_MD)
        title = QLabel("Pending Task Reminders")
        set_label_point_size(title, FONT_SIZE_TITLE_MD)
        title.setStyleSheet(f"font-weight: bold; color: {tc}; background: transparent; border: none;")
        header.addWidget(title, 1)
        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(*REMINDERS_LIST_CLOSE_BTN_SIZE)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {tmc};
                border: none;
                font-size: {FONT_SIZE_LABEL_MD}px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {tc};
                background: {hover};
                border-radius: {RADIUS_SMALL}px;
            }}
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(PRIORITY_DIVIDER_HEIGHT)
        sep.setStyleSheet(f"background: {border_c}; border: none;")
        layout.addWidget(sep)

        if not pending:
            empty_label = QLabel("No pending reminders.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"color: {tmc}; padding: 8px 0; background: transparent; border: none;")
            layout.addWidget(empty_label)
            self.setFixedSize(*REMINDERS_LIST_EMPTY_STATE_SIZE)
        else:
            reminder_list = QListWidget()
            reminder_list.setMinimumHeight(REMINDERS_LIST_MIN_HEIGHT)
            item_r = SPACING_SM
            reminder_list.setStyleSheet(f"""
                QListWidget {{
                    background-color: {input_bg};
                    color: {tc};
                    border: 1px solid {border_c};
                    border-radius: {item_r}px;
                    padding: 4px;
                    outline: none;
                    font-size: {FONT_SIZE_BODY}px;
                }}
                QListWidget::item {{
                    background-color: transparent;
                    color: {tc};
                    padding: 8px 10px;
                    border-radius: {item_r}px;
                    min-height: 22px;
                }}
                QListWidget::item:hover {{
                    background-color: {hover};
                }}
                QListWidget::item:selected {{
                    background-color: {hover_strong};
                    color: {tc};
                }}
            """)
            pal = reminder_list.palette()
            pal.setColor(QPalette.ColorRole.Highlight, QColor(hover_strong))
            pal.setColor(QPalette.ColorRole.HighlightedText, QColor(tc))
            pal.setColor(QPalette.ColorRole.Base, QColor(input_bg))
            pal.setColor(QPalette.ColorRole.Text, QColor(tc))
            reminder_list.setPalette(pal)

            for cfg_dict, label in pending:
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, cfg_dict.get("taskId"))
                reminder_list.addItem(item)

            layout.addWidget(reminder_list, 1)

            cancel_btn = QPushButton("Cancel Selected")
            cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cancel_btn.setMinimumHeight(TIMER_DIALOG_BTN_HEIGHT)
            cancel_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {input_bg};
                    color: {tc};
                    border: 1px solid {border_c};
                    border-radius: {SPACING_SM}px;
                    padding: 6px 16px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {hover};
                    border-color: {_c(theme, "border_highlight")};
                }}
                QPushButton:pressed {{
                    background-color: {hover_strong};
                }}
                QPushButton:disabled {{
                    color: {tmc};
                    border-color: {border_c};
                }}
            """)
            cancel_btn.clicked.connect(lambda: self._cancel_selected(reminder_list))
            layout.addWidget(cancel_btn)
            self.setFixedSize(*REMINDERS_LIST_FILLED_STATE_SIZE)

        def _on_focus_changed(old, new):
            if self is None or not self.isVisible():
                return
            if new is None:
                return
            w = new
            while w is not None:
                if w is self:
                    return
                w = w.parent()
            self.close()

        app = QApplication.instance()
        app.focusChanged.connect(_on_focus_changed)
        self._focus_cleanup = _on_focus_changed

        if self._ctx.screen:
            screen = self._ctx.screen()
            available = screen.availableGeometry() if screen else None
        else:
            available = None
        if available is not None and self._ctx.frame_geometry:
            main_rect = self._ctx.frame_geometry()
            dlg_w = self.width()
            dlg_h = self.height()
            gap = DIALOG_PLACEMENT_GAP
            x = main_rect.right() + gap
            y = main_rect.top()
            if x + dlg_w > available.right():
                x = main_rect.left() - gap - dlg_w
            if x < available.left():
                x = available.left()
            y = max(available.top(), min(y, available.bottom() - dlg_h))
            self.move(x, y)

    def _cancel_selected(self, reminder_list: QListWidget) -> None:
        """Cancel all selected reminders."""
        for item in reminder_list.selectedItems():
            tid = item.data(Qt.ItemDataRole.UserRole)
            self._ctx.timer_manager.cancel_task_reminder(tid)
            self._ctx.app_state["timers"] = self._ctx.timer_manager.to_list()
            self._ctx.state_manager.save()
            reminder_list.takeItem(reminder_list.row(item))
        if reminder_list.count() == 0:
            self.close()

    def closeEvent(self, event) -> None:
        """Clean up focus watcher."""
        if self._focus_cleanup:
            app = QApplication.instance()
            if app:
                try:
                    app.focusChanged.disconnect(self._focus_cleanup)
                except (TypeError, RuntimeError):
                    pass
        super().closeEvent(event)
