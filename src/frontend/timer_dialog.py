"""Manage countdown/repeat reminders — themed glass-panel dialog."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.theme import normalize_theme_id
from src.constants import (
    BTN_HEIGHT_MD,
    BTN_MIN_WIDTH_MD,
    FONT_SIZE_TITLE_MD,
    KEY_SEQ_EDIT_WIDTH,
    MARGIN_STANDARD,
    SECONDS_PER_MINUTE,
    SPACING_LG,
    SPACING_MD,
    TIMER_DEFAULT_INTERVAL_S,
    TIMER_DIALOG_BTN_HEIGHT,
    TIMER_DIALOG_DEFAULT,
    TIMER_DIALOG_MIN,
    TIMER_EDIT_DIALOG_DEFAULT,
    TIMER_EDIT_DIALOG_MIN_WIDTH,
    TIMER_MAIN_LAYOUT_MARGINS,
    TIMER_MAX_INTERVAL_MIN,
    TIMER_MIN_INTERVAL_MIN,
)


class TimerDialog(GlassPanelDialog):
    """Add, edit, enable/disable, and remove reminder timers."""

    def __init__(self, timer_manager, parent=None):
        super().__init__(parent, escape_action="accept")
        self._timer_manager = timer_manager

        self.setWindowTitle("Reminders \u2014 Nudge")
        self.resize(*TIMER_DIALOG_DEFAULT)
        self.setMinimumSize(*TIMER_DIALOG_MIN)

        self._build_ui()
        self._refresh_list()
        self._update_overlap_opacity()

    def _get_theme_id(self) -> str:
        parent = self.parent()
        if parent is None:
            return normalize_theme_id(getattr(self, "app_state", {}).get("theme", "dark"))
        return normalize_theme_id(getattr(parent, "app_state", {}).get("theme", "dark"))

    def _build_ui(self):
        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*TIMER_MAIN_LAYOUT_MARGINS)
        layout.setSpacing(SPACING_LG)

        title = QLabel("Reminders")
        title.setStyleSheet(f"font-weight: bold; font-size: {FONT_SIZE_TITLE_MD}px;")
        layout.addWidget(title)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._edit_selected)
        layout.addWidget(self._list, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING_MD)

        add_btn = QPushButton("Add")
        add_btn.setObjectName("primaryButton")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add)
        btn_row.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("primaryButton")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(self._edit_selected)
        btn_row.addWidget(edit_btn)

        self._toggle_btn = QPushButton("Enable / Disable")
        self._toggle_btn.setObjectName("primaryButton")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle_selected)
        btn_row.addWidget(self._toggle_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.setObjectName("primaryButton")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(self._remove_selected)
        btn_row.addWidget(remove_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _refresh_list(self):
        self._list.clear()
        for cfg in self._timer_manager.to_list():
            status = "ON" if cfg["enabled"] else "OFF"
            repeat = "repeats" if cfg["repeat"] else "once"
            mins = cfg["intervalSeconds"] // SECONDS_PER_MINUTE
            secs = cfg["intervalSeconds"] % SECONDS_PER_MINUTE
            interval = f"{mins}m" if secs == 0 else f"{mins}m{secs}s"
            label = f"[{status}] {cfg['name']} \u2014 every {interval} ({repeat})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, cfg["timerId"])
            self._list.addItem(item)

    def _add(self):
        dlg = _TimerEditDialog(self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self._timer_manager.add(dlg.name(), dlg.interval(), dlg.repeat())
            self._refresh_list()

    def _edit_selected(self, _=None):
        item = self._list.currentItem()
        if item is None:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        raw = [c for c in self._timer_manager.to_list() if c["timerId"] == tid]
        if not raw:
            return
        cfg = raw[0]
        dlg = _TimerEditDialog(self, name=cfg["name"], interval=cfg["intervalSeconds"], repeat=cfg["repeat"])
        if dlg.exec() == dlg.DialogCode.Accepted:
            self._timer_manager.remove(tid)
            self._timer_manager.add(dlg.name(), dlg.interval(), dlg.repeat())
            self._refresh_list()

    def _toggle_selected(self):
        item = self._list.currentItem()
        if item is None:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        raw = [c for c in self._timer_manager.to_list() if c["timerId"] == tid]
        if not raw:
            return
        self._timer_manager.set_enabled(tid, not raw[0]["enabled"])
        self._refresh_list()

    def _remove_selected(self):
        item = self._list.currentItem()
        if item is None:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        self._timer_manager.remove(tid)
        self._refresh_list()


class _TimerEditDialog(GlassPanelDialog):
    """Inline form for adding or editing a single timer."""

    def __init__(self, parent=None, name="", interval=TIMER_DEFAULT_INTERVAL_S, repeat=False):
        super().__init__(parent, escape_action="reject")

        self.setWindowTitle("Edit Reminder \u2014 Nudge")
        self.resize(*TIMER_EDIT_DIALOG_DEFAULT)
        self.setMinimumWidth(TIMER_EDIT_DIALOG_MIN_WIDTH)

        self._build_ui(name, interval, repeat)
        self._update_overlap_opacity()

    def _build_ui(self, name, interval, repeat):
        outer = QVBoxLayout(self.bg_frame)
        outer.setContentsMargins(*MARGIN_STANDARD)
        outer.setSpacing(SPACING_LG)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(SPACING_LG)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._name_edit = QLineEdit(name or "Reminder")
        self._name_edit.setMinimumHeight(BTN_HEIGHT_MD)
        form.addRow("Name:", self._name_edit)

        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(TIMER_MIN_INTERVAL_MIN, TIMER_MAX_INTERVAL_MIN)
        self._interval_spin.setValue(interval // SECONDS_PER_MINUTE if interval >= SECONDS_PER_MINUTE else TIMER_MIN_INTERVAL_MIN)
        self._interval_spin.setSuffix(" minutes")
        self._interval_spin.setMinimumHeight(BTN_HEIGHT_MD)
        self._interval_spin.setMinimumWidth(KEY_SEQ_EDIT_WIDTH)
        form.addRow("Every:", self._interval_spin)

        outer.addLayout(form)

        self._repeat_cb = QCheckBox("Repeat (keep firing)")
        self._repeat_cb.setChecked(repeat)
        outer.addWidget(self._repeat_cb)

        outer.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING_MD)
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primaryButton")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setFixedHeight(TIMER_DIALOG_BTN_HEIGHT)
        ok_btn.setMinimumWidth(BTN_MIN_WIDTH_MD)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("primaryButton")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedHeight(TIMER_DIALOG_BTN_HEIGHT)
        cancel_btn.setMinimumWidth(BTN_MIN_WIDTH_MD)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        outer.addLayout(btn_row)

    def name(self) -> str:
        return self._name_edit.text().strip() or "Reminder"

    def interval(self) -> int:
        return self._interval_spin.value() * SECONDS_PER_MINUTE

    def repeat(self) -> bool:
        return self._repeat_cb.isChecked()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept()
            event.accept()
        else:
            super().keyPressEvent(event)
