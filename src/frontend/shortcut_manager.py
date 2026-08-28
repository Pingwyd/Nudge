"""Manages keyboard shortcut registration and lifecycle."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt

from src.constants import TOGGLE_GROUPS_SHORTCUT, UNDO_SHORTCUT

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
        tray_seq_str = app_state.get("toggleTrayShortcut", "Ctrl+M") or "Ctrl+M"
        tray_sequence = QKeySequence.fromString(tray_seq_str, QKeySequence.SequenceFormat.PortableText)
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
            self._bind_tray_shortcut(tray_seq_str, tray_sequence)

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

        # Toggle task groups — fixed shortcut, not configurable
        self._shortcuts["toggle_groups"] = QShortcut(
            QKeySequence(TOGGLE_GROUPS_SHORTCUT), self._mw
        )
        self._shortcuts["toggle_groups"].setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self._shortcuts["toggle_groups"].activated.connect(
            self._mw._toggle_groups_via_shortcut
        )

        # Undo last completion — fixed shortcut, not configurable
        self._shortcuts["undo"] = QShortcut(
            QKeySequence(UNDO_SHORTCUT), self._mw
        )
        self._shortcuts["undo"].setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self._shortcuts["undo"].activated.connect(
            self._mw._undo_last_archive
        )

    def _bind_tray_shortcut(self, seq_str: str, tray_sequence: QKeySequence) -> None:
        """Global hotkey (works while hidden) + Qt shortcut fallback (while focused)."""
        from PyQt6.QtWidgets import QApplication

        # Parent to the QApplication so the shortcut works whenever *any*
        # Nudge window is active (ApplicationShortcut on MainWindow alone can
        # miss keypresses when a child dialog / frameless focus quirk applies).
        app = QApplication.instance()
        parent = app if app is not None else self._mw
        self._shortcuts["tray"] = QShortcut(tray_sequence, parent)
        self._shortcuts["tray"].setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._shortcuts["tray"].activated.connect(self._mw._toggle_tray_visibility)

        hid = self._mw._hotkey_filter.register(seq_str, self._mw._toggle_tray_visibility)
        if hid is not None:
            self._mw._tray_hotkey_id = hid
        else:
            self._mw._tray_hotkey_id = None
            logger.warning(
                "Tray global hotkey %r unavailable; Qt shortcut fallback is active while focused",
                seq_str,
            )

    def suspend_tray_hotkey(self) -> None:
        """Temporarily drop the global tray hotkey (e.g. while editing it in Settings)."""
        if self._mw._tray_hotkey_id is not None:
            self._mw._hotkey_filter.unregister(self._mw._tray_hotkey_id)
            self._mw._tray_hotkey_id = None
        tray_sc = self._shortcuts.get("tray")
        if tray_sc is not None:
            tray_sc.setEnabled(False)

    def resume_tray_hotkey(self, seq_str: str | None = None) -> None:
        """Re-bind tray hotkey after Settings finishes editing the chord."""
        app_state = self._mw.app_state
        if not seq_str:
            seq_str = app_state.get("toggleTrayShortcut", "Ctrl+M") or "Ctrl+M"
        tray_sequence = QKeySequence.fromString(seq_str, QKeySequence.SequenceFormat.PortableText)
        if tray_sequence.isEmpty():
            return

        # Drop any prior global registration before binding again.
        if self._mw._tray_hotkey_id is not None:
            self._mw._hotkey_filter.unregister(self._mw._tray_hotkey_id)
            self._mw._tray_hotkey_id = None

        old = self._shortcuts.pop("tray", None)
        if old is not None:
            try:
                old.setParent(None)
                old.deleteLater()
            except RuntimeError:
                pass

        self._bind_tray_shortcut(seq_str, tray_sequence)

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
