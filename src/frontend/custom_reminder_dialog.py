"""Custom reminder dialog for setting task reminders."""
from __future__ import annotations
import logging
import re as _re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from PyQt6.QtCore import QDate, QTime, Qt
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)
from PyQt6.QtWidgets import QMessageBox as _MB

from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.theme import get_theme, normalize_theme_id, refresh_glass_shells
from src.constants import (
    BTN_HEIGHT_MD,
    BTN_HEIGHT_SM,
    DATE_EDIT_MIN_WIDTH,
    DURATION_APPLY_BTN_WIDTH,
    DURATION_INPUT_MIN_WIDTH,
    FONT_SIZE_BODY,
    FONT_SIZE_HINT,
    FONT_SIZE_LABEL_SM,
    REMINDER_BUTTON_SPACING,
    REMINDER_DEFAULT_HOUR,
    REMINDER_DEFAULT_MINUTE,
    REMINDER_DEFAULT_REPEAT_MIN,
    REMINDER_DIALOG_DEFAULT,
    REMINDER_DIALOG_MIN,
    REMINDER_MAIN_LAYOUT_MARGINS,
    REMINDER_OVERLAP_RADIUS,
    REPEAT_SPIN_WIDTH,
    SPACING_MD,
    SPACING_SM,
    TIME_EDIT_MIN_WIDTH,
    TIMER_MAX_INTERVAL_MIN,
    TIMER_MIN_INTERVAL_MIN,
)

if TYPE_CHECKING:
    from src.frontend.dialog_context import DialogContext

logger = logging.getLogger(__name__)


class CustomReminderDialog(GlassPanelDialog):
    """Dialog for setting a custom reminder on a task."""

    def __init__(self, ctx: DialogContext, task_ref: dict, parent: QWidget | None = None):
        super().__init__(parent=parent, overlap_radius=REMINDER_OVERLAP_RADIUS, escape_action="reject")
        self._ctx = ctx
        self._task_ref = task_ref
        self.setWindowTitle("Set Reminder — Nudge")
        self.resize(*REMINDER_DIALOG_DEFAULT)
        self.setMinimumSize(*REMINDER_DIALOG_MIN)
        self._build_ui()
        self._position_dialog()

    def _build_ui(self) -> None:
        theme_id = normalize_theme_id(self._ctx.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)

        frame = self.bg_frame
        frame.setGeometry(0, 0, *REMINDER_DIALOG_DEFAULT)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(*REMINDER_MAIN_LAYOUT_MARGINS)
        layout.setSpacing(SPACING_SM)

        title = QLabel("Set Reminder")
        title.setStyleSheet(f"font-weight: bold; font-size: {FONT_SIZE_BODY}px;")
        layout.addWidget(title)

        current_reminder_label = None
        existing_cfg = self._ctx.timer_manager.get_timer_for_task(self._task_ref["id"])
        if existing_cfg is not None:
            existing_dt = datetime.fromtimestamp(existing_cfg.next_trigger_at)
            current_reminder_label = QLabel(f"Current reminder: {existing_dt.strftime('%A, %d %b %Y at %H:%M')}")
            current_reminder_label.setStyleSheet(f"font-size: {FONT_SIZE_LABEL_SM}px; color: rgba(255,255,255,120); font-style: italic;")
            current_reminder_label.setWordWrap(True)
            layout.addWidget(current_reminder_label)

        presets_label = QLabel("Quick set:")
        presets_label.setStyleSheet(f"font-size: {FONT_SIZE_LABEL_SM}px; color: rgba(255,255,255,160);")
        layout.addWidget(presets_label)

        duration_row = QHBoxLayout()
        duration_row.setSpacing(SPACING_SM)
        duration_input = QLineEdit()
        duration_input.setPlaceholderText("e.g. 25 minutes, 2 hours, 3 days...")
        duration_input.setMinimumWidth(DURATION_INPUT_MIN_WIDTH)
        duration_row.addWidget(duration_input, 1)
        duration_apply = QPushButton("Set")
        duration_apply.setObjectName("ghostButton")
        duration_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        duration_apply.setFixedSize(DURATION_APPLY_BTN_WIDTH, BTN_HEIGHT_SM)
        duration_row.addWidget(duration_apply)
        layout.addLayout(duration_row)

        quickset_hint = QLabel("Type a shortcut or use the pickers above — both update together.")
        quickset_hint.setStyleSheet(f"font-size: {FONT_SIZE_HINT}px; color: rgba(255,255,255,100);")
        layout.addWidget(quickset_hint)

        dt_label = QLabel("When:")
        dt_label.setStyleSheet(f"font-size: {FONT_SIZE_LABEL_SM}px; color: rgba(255,255,255,160);")
        layout.addWidget(dt_label)

        dt_row = QHBoxLayout()
        dt_row.setSpacing(SPACING_MD)

        existing_cfg = self._ctx.timer_manager.get_timer_for_task(self._task_ref["id"])
        if existing_cfg is not None:
            existing_dt = datetime.fromtimestamp(existing_cfg.next_trigger_at)
            initial_date = QDate(existing_dt.year, existing_dt.month, existing_dt.day)
            initial_time = QTime(existing_dt.hour, existing_dt.minute)
        else:
            initial_date = QDate.currentDate().addDays(1)
            initial_time = QTime(REMINDER_DEFAULT_HOUR, REMINDER_DEFAULT_MINUTE)

        date_edit = QDateEdit(initial_date)
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("MMM d, yyyy")
        date_edit.setMinimumDate(QDate.currentDate())
        date_edit.setMinimumWidth(DATE_EDIT_MIN_WIDTH)
        dt_row.addWidget(date_edit)

        time_edit = QTimeEdit(initial_time)
        time_edit.setDisplayFormat("hh:mm AP")
        time_edit.setMinimumWidth(TIME_EDIT_MIN_WIDTH)
        dt_row.addWidget(time_edit)

        dt_row.addStretch()
        layout.addLayout(dt_row)

        preview_label = QLabel()
        preview_label.setStyleSheet(f"font-size: {FONT_SIZE_LABEL_SM}px; color: rgba(255,255,255,180); font-weight: 500;")
        preview_label.setWordWrap(True)
        layout.addWidget(preview_label)

        _computed_target = [None]

        confirm_label = QLabel()
        confirm_label.setStyleSheet(f"font-size: {FONT_SIZE_LABEL_SM}px; color: #4ade80; font-weight: 600;")
        confirm_label.hide()
        layout.addWidget(confirm_label)

        repeat_row = QHBoxLayout()
        repeat_row.setSpacing(SPACING_SM)
        repeat_cb = QCheckBox("Repeat every")
        repeat_row.addWidget(repeat_cb)

        repeat_spin = QSpinBox()
        repeat_spin.setRange(TIMER_MIN_INTERVAL_MIN, TIMER_MAX_INTERVAL_MIN)
        repeat_spin.setValue(REMINDER_DEFAULT_REPEAT_MIN)
        repeat_spin.setSuffix(" min")
        repeat_spin.setFixedWidth(REPEAT_SPIN_WIDTH)
        repeat_spin.setEnabled(False)
        repeat_cb.toggled.connect(repeat_spin.setEnabled)
        repeat_row.addWidget(repeat_spin)
        repeat_row.addStretch()
        layout.addLayout(repeat_row)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(REMINDER_BUTTON_SPACING)
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedHeight(BTN_HEIGHT_MD)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        set_btn = QPushButton("Set")
        set_btn.setObjectName("primaryButton")
        set_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        set_btn.setFixedHeight(BTN_HEIGHT_MD)
        set_btn.clicked.connect(self.accept)
        btn_row.addWidget(set_btn)
        layout.addLayout(btn_row)

        def _update_preview():
            q_date = date_edit.date()
            q_time = time_edit.time()
            target = datetime(q_date.year(), q_date.month(), q_date.day(),
                              q_time.hour(), q_time.minute())
            preview_label.setText(f"Will remind at: {target.strftime('%A, %d %b %Y at %H:%M')}")

        def _on_picker_changed(_):
            _computed_target[0] = None
            _update_preview()

        date_edit.dateChanged.connect(_on_picker_changed)
        time_edit.timeChanged.connect(_on_picker_changed)
        _update_preview()

        def _parse_duration():
            text = duration_input.text().strip().lower()
            if not text:
                return
            match = _re.match(r"(\d+)\s*(m|min|mins|minutes|h|hr|hrs|hours|d|day|days)?", text)
            if not match:
                return
            amount = int(match.group(1))
            unit = (match.group(2) or "m").lower()
            if unit in ("d", "day", "days"):
                delta = timedelta(days=amount)
            elif unit in ("h", "hr", "hrs", "hours", "hour"):
                delta = timedelta(hours=amount)
            else:
                delta = timedelta(minutes=amount)
            target = datetime.now() + delta
            _computed_target[0] = target
            date_edit.setDate(QDate(target.year, target.month, target.day))
            time_edit.setTime(QTime(target.hour, target.minute))
            _update_preview()

        duration_input.textChanged.connect(lambda _: _parse_duration())
        duration_apply.clicked.connect(_parse_duration)
        duration_input.returnPressed.connect(_parse_duration)

        self._date_edit = date_edit
        self._time_edit = time_edit
        self._repeat_cb = repeat_cb
        self._repeat_spin = repeat_spin
        self._computed_target = _computed_target

    def _position_dialog(self) -> None:
        if self._ctx.window_rects_to_avoid and self._ctx.place_dialog_avoiding_rects:
            avoid = self._ctx.window_rects_to_avoid()
            self._ctx.place_dialog_avoiding_rects(self, avoid)

        theme_id = normalize_theme_id(self._ctx.app_state.get("theme", "dark"))
        refresh_glass_shells(self, theme_id)

    def accept(self) -> None:
        if self._computed_target[0] is not None:
            reminder_dt = self._computed_target[0]
            self._computed_target[0] = None
        else:
            q_date = self._date_edit.date()
            q_time = self._time_edit.time()
            reminder_dt = datetime(
                q_date.year(), q_date.month(), q_date.day(),
                q_time.hour(), q_time.minute(), q_time.second(),
            )
        if reminder_dt <= datetime.now():
            _MB.warning(self, "Invalid Time", "Reminder time must be in the future.")
            return
        task_ref = self._task_ref
        self._ctx.timer_manager.cancel_task_reminder(task_ref["id"])
        self._ctx.timer_manager.add_task_reminder(
            task_id=task_ref["id"],
            name=task_ref.get("text", "Task reminder"),
            trigger_at=reminder_dt,
            repeat_minutes=self._repeat_spin.value() if self._repeat_cb.isChecked() else 0,
        )
        self._ctx.app_state["timers"] = self._ctx.timer_manager.to_list()
        self._ctx.state_manager.save()
        row = self._ctx.task_row_widgets.get(id(task_ref))
        if row is not None:
            row.set_task_ref(task_ref)
        super().accept()
