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


class TimerDialog(GlassPanelDialog):
    """Add, edit, enable/disable, and remove reminder timers."""

    def __init__(self, timer_manager, parent=None):
        super().__init__(parent, escape_action="accept")
        self._timer_manager = timer_manager

        self.setWindowTitle("Reminders \u2014 Nudge")
        self.resize(480, 340)
        self.setMinimumSize(400, 280)

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
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Reminders")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._edit_selected)
        layout.addWidget(self._list, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

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
            mins = cfg["intervalSeconds"] // 60
            secs = cfg["intervalSeconds"] % 60
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

    def __init__(self, parent=None, name="", interval=300, repeat=False):
        super().__init__(parent, escape_action="reject")

        self.setWindowTitle("Edit Reminder \u2014 Nudge")
        self.resize(320, 200)
        self.setMinimumWidth(280)

        self._build_ui(name, interval, repeat)
        self._update_overlap_opacity()

    def _build_ui(self, name, interval, repeat):
        outer = QVBoxLayout(self.bg_frame)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(10)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._name_edit = QLineEdit(name or "Reminder")
        self._name_edit.setMinimumHeight(28)
        form.addRow("Name:", self._name_edit)

        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 1440)
        self._interval_spin.setValue(interval // 60 if interval >= 60 else 1)
        self._interval_spin.setSuffix(" minutes")
        self._interval_spin.setMinimumHeight(28)
        self._interval_spin.setMinimumWidth(120)
        form.addRow("Every:", self._interval_spin)

        outer.addLayout(form)

        self._repeat_cb = QCheckBox("Repeat (keep firing)")
        self._repeat_cb.setChecked(repeat)
        outer.addWidget(self._repeat_cb)

        outer.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primaryButton")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setFixedHeight(30)
        ok_btn.setMinimumWidth(70)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("primaryButton")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedHeight(30)
        cancel_btn.setMinimumWidth(70)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        outer.addLayout(btn_row)

    def name(self) -> str:
        return self._name_edit.text().strip() or "Reminder"

    def interval(self) -> int:
        return self._interval_spin.value() * 60

    def repeat(self) -> bool:
        return self._repeat_cb.isChecked()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept()
            event.accept()
        else:
            super().keyPressEvent(event)
