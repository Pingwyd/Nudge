"""Manages keyboard shortcut registration and lifecycle."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ShortcutManager:
    """Registers and updates keyboard shortcuts from app_state."""

    def __init__(self, main_window: Any):
        self._mw = main_window
        self._shortcuts: dict[str, Any] = {}

    def register_all(self) -> None:
        """Register all shortcuts from app_state."""
        self.update_shortcuts()

    def update_shortcuts(self) -> None:
        """Destroy old shortcuts and create new ones from app_state."""
        app_state = self._mw.app_state

        history_sequence = QKeySequence.fromString(app_state.get("historyShortcut", "Ctrl+H"), QKeySequence.SequenceFormat.PortableText)
        settings_sequence = QKeySequence.fromString(app_state.get("settingsShortcut", "Ctrl+,"), QKeySequence.SequenceFormat.PortableText)
        pin_sequence = QKeySequence.fromString(app_state.get("pinShortcut", "Ctrl+P"), QKeySequence.SequenceFormat.PortableText)
        aot_sequence = QKeySequence.fromString(app_state.get("alwaysOnTopShortcut", "Alt+T"), QKeySequence.SequenceFormat.PortableText)
        export_sequence = QKeySequence.fromString(app_state.get("exportShortcut", "Ctrl+E"), QKeySequence.SequenceFormat.PortableText)
        tray_sequence = QKeySequence.fromString(app_state.get("toggleTrayShortcut", "Ctrl+M"), QKeySequence.SequenceFormat.PortableText)
        reminders_sequence = QKeySequence.fromString(app_state.get("remindersShortcut", ""), QKeySequence.SequenceFormat.PortableText)

        self.destroy_all()

        self._shortcuts["history"] = QShortcut(history_sequence, self._mw)
        self._shortcuts["history"].setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts["history"].activated.connect(self._mw.open_history)

        self._shortcuts["settings"] = QShortcut(settings_sequence, self._mw)
        self._shortcuts["settings"].setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts["settings"].activated.connect(self._mw.open_settings)

        self._shortcuts["pin"] = QShortcut(pin_sequence, self._mw)
        self._shortcuts["pin"].setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._shortcuts["pin"].activated.connect(self._mw.toggle_pinned_to_desktop)

        if not aot_sequence.isEmpty():
            self._shortcuts["always_on_top"] = QShortcut(aot_sequence, self._mw)
            self._shortcuts["always_on_top"].setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            self._shortcuts["always_on_top"].activated.connect(self._mw._toggle_always_on_top_via_shortcut)

        if not tray_sequence.isEmpty():
            hid = self._mw._hotkey_filter.register(
                app_state.get("toggleTrayShortcut", "Ctrl+M"),
                self._mw._toggle_tray_visibility,
            )
            if hid is not None:
                self._mw._tray_hotkey_id = hid

        if not export_sequence.isEmpty():
            self._shortcuts["export"] = QShortcut(export_sequence, self._mw)
            self._shortcuts["export"].setContext(Qt.ShortcutContext.ApplicationShortcut)
            self._shortcuts["export"].activated.connect(self._mw._open_export_via_shortcut)

        if not reminders_sequence.isEmpty():
            self._shortcuts["reminders"] = QShortcut(reminders_sequence, self._mw)
            self._shortcuts["reminders"].setContext(Qt.ShortcutContext.ApplicationShortcut)
            self._shortcuts["reminders"].activated.connect(self._mw.open_reminders)

        # Clipboard import — fixed shortcut, not configurable
        self._shortcuts["clipboard_import"] = QShortcut(
            QKeySequence("Ctrl+Shift+V"), self._mw
        )
        self._shortcuts["clipboard_import"].setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self._shortcuts["clipboard_import"].activated.connect(
            self._mw._on_clipboard_import
        )

    def destroy_all(self) -> None:
        """Clean up all shortcut objects."""
        for sc in self._shortcuts.values():
            try:
                sc.setParent(None)
                sc.deleteLater()
            except RuntimeError:
                pass
        self._shortcuts.clear()

        if self._mw._tray_hotkey_id is not None:
            self._mw._hotkey_filter.unregister(self._mw._tray_hotkey_id)
            self._mw._tray_hotkey_id = None
