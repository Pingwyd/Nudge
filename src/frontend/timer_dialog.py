"""Manage countdown/repeat reminders."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
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


class TimerDialog(QDialog):
    """Add, edit, enable/disable, and remove reminder timers."""

    def __init__(self, timer_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reminders")
        self.setMinimumSize(360, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._manager = timer_manager
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._edit_selected)
        layout.addWidget(self._list, 1)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add)
        btn_row.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._edit_selected)
        btn_row.addWidget(edit_btn)

        self._toggle_btn = QPushButton("Enable / Disable")
        self._toggle_btn.clicked.connect(self._toggle_selected)
        btn_row.addWidget(self._toggle_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_selected)
        btn_row.addWidget(remove_btn)

        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)
        self._refresh_list()

    def _refresh_list(self):
        self._list.clear()
        for cfg in self._manager.to_list():
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
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._manager.add(dlg.name(), dlg.interval(), dlg.repeat())
            self._refresh_list()

    def _edit_selected(self, _=None):
        item = self._list.currentItem()
        if item is None:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        raw = [c for c in self._manager.to_list() if c["timerId"] == tid]
        if not raw:
            return
        cfg = raw[0]
        dlg = _TimerEditDialog(self, name=cfg["name"], interval=cfg["intervalSeconds"], repeat=cfg["repeat"])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Remove and re-add with updated values
            self._manager.remove(tid)
            self._manager.add(dlg.name(), dlg.interval(), dlg.repeat())
            self._refresh_list()

    def _toggle_selected(self):
        item = self._list.currentItem()
        if item is None:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        raw = [c for c in self._manager.to_list() if c["timerId"] == tid]
        if not raw:
            return
        self._manager.set_enabled(tid, not raw[0]["enabled"])
        self._refresh_list()

    def _remove_selected(self):
        item = self._list.currentItem()
        if item is None:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        self._manager.remove(tid)
        self._refresh_list()


class _TimerEditDialog(QDialog):
    """Inline form for adding or editing a single timer."""

    def __init__(self, parent=None, name="", interval=300, repeat=False):
        super().__init__(parent)
        self.setWindowTitle("Timer")
        self.setMinimumWidth(280)

        layout = QFormLayout(self)

        self._name_edit = QLineEdit(name or "Reminder")
        layout.addRow("Name:", self._name_edit)

        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 1440)
        self._interval_spin.setValue(interval // 60 if interval >= 60 else 1)
        self._interval_spin.setSuffix(" minutes")
        layout.addRow("Every:", self._interval_spin)

        self._repeat_cb = QCheckBox("Repeat (keep firing)")
        self._repeat_cb.setChecked(repeat)
        layout.addRow(self._repeat_cb)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(ok_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addRow(btn_row)

    def name(self) -> str:
        return self._name_edit.text().strip() or "Reminder"

    def interval(self) -> int:
        return self._interval_spin.value() * 60

    def repeat(self) -> bool:
        return self._repeat_cb.isChecked()
