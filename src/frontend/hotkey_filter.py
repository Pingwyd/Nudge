"""Global hotkey event filter."""

import ctypes
import logging
from ctypes import wintypes

from PyQt6.QtCore import QAbstractNativeEventFilter, QObject, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence

logger = logging.getLogger(__name__)

WM_HOTKEY = 0x0312
WM_THEMECHANGED = 0x031A
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
ERROR_HOTKEY_ALREADY_REGISTERED = 1409


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class _HotkeySignals(QObject):
    """Separate QObject so the filter itself is not multi-inherited (PyQt MI
    with QAbstractNativeEventFilter can silently stop delivering events)."""
    theme_changed = pyqtSignal()
    hotkey_activated = pyqtSignal(int)


class GlobalHotkeyFilter(QAbstractNativeEventFilter):
    """Win32 RegisterHotKey → Qt native event filter.

    Hotkeys are bound to the main window HWND (the approach that worked before
    the NULL-hwnd change). Call set_hwnd() whenever setWindowFlags recreates
    the native window so registrations are moved to the new handle.
    """

    def __init__(self):
        super().__init__()
        self._signals = _HotkeySignals()
        # Public aliases used by MainWindow
        self.theme_changed = self._signals.theme_changed
        self.hotkey_activated = self._signals.hotkey_activated

        self._callbacks = {}       # id -> callable
        self._bindings = {}        # id -> (mod, vk, key_sequence_str)
        self._next_id = 1000
        self._hwnd = None

        self._signals.hotkey_activated.connect(
            self._dispatch, Qt.ConnectionType.QueuedConnection
        )

    def set_hwnd(self, hwnd):
        """Bind (or re-bind) all hotkeys to a window handle.

        Pass the current ``int(widget.winId())`` after show / setWindowFlags.
        """
        hwnd = int(hwnd) if hwnd else None
        if hwnd == self._hwnd:
            return
        self._unregister_all_win32()
        self._hwnd = hwnd
        self._register_all_win32()

    def register(self, key_sequence_str, callback):
        seq = QKeySequence.fromString(key_sequence_str, QKeySequence.SequenceFormat.PortableText)
        if seq.isEmpty():
            return None
        key = seq[0]
        qt_mods = key.keyboardModifiers()
        mod = 0
        if qt_mods & Qt.KeyboardModifier.ControlModifier:
            mod |= MOD_CONTROL
        if qt_mods & Qt.KeyboardModifier.AltModifier:
            mod |= MOD_ALT
        if qt_mods & Qt.KeyboardModifier.ShiftModifier:
            mod |= MOD_SHIFT
        if qt_mods & Qt.KeyboardModifier.MetaModifier:
            mod |= MOD_WIN
        vk = int(key.key())
        hotkey_id = self._next_id
        self._next_id += 1

        if not self._win32_register(hotkey_id, mod, vk, key_sequence_str):
            return None

        self._callbacks[hotkey_id] = callback
        self._bindings[hotkey_id] = (mod, vk, key_sequence_str)
        return hotkey_id

    def unregister(self, hotkey_id):
        if hotkey_id is None:
            return
        self._win32_unregister(hotkey_id)
        self._callbacks.pop(hotkey_id, None)
        self._bindings.pop(hotkey_id, None)

    def unregister_all(self):
        for hid in list(self._callbacks):
            self.unregister(hid)

    def _win32_register(self, hotkey_id, mod, vk, key_sequence_str):
        hwnd = self._hwnd  # may be None before first set_hwnd
        ctypes.windll.kernel32.SetLastError(0)
        if not ctypes.windll.user32.RegisterHotKey(hwnd, hotkey_id, mod, vk):
            err = ctypes.windll.kernel32.GetLastError()
            if err == ERROR_HOTKEY_ALREADY_REGISTERED:
                logger.warning(
                    "RegisterHotKey failed for %r (id=%s, hwnd=%s): already registered",
                    key_sequence_str, hotkey_id, hwnd,
                )
            else:
                logger.warning(
                    "RegisterHotKey failed for %r (id=%s, hwnd=%s): Win32 error %s",
                    key_sequence_str, hotkey_id, hwnd, err,
                )
            return False
        return True

    def _win32_unregister(self, hotkey_id):
        ctypes.windll.user32.UnregisterHotKey(self._hwnd, hotkey_id)

    def _unregister_all_win32(self):
        for hid in list(self._bindings):
            self._win32_unregister(hid)

    def _register_all_win32(self):
        for hid, (mod, vk, seq_str) in list(self._bindings.items()):
            if not self._win32_register(hid, mod, vk, seq_str):
                # Leave callback in place; Qt QShortcut fallback may still work.
                logger.warning("Failed to re-bind hotkey id=%s after HWND change", hid)

    def _dispatch(self, hotkey_id: int):
        cb = self._callbacks.get(int(hotkey_id))
        if cb:
            try:
                cb()
            except Exception:
                logger.exception("Global hotkey callback failed (id=%s)", hotkey_id)

    def nativeEventFilter(self, eventType, message):
        etype = bytes(eventType)
        # HWND-bound hotkeys arrive as windows_generic_MSG; NULL-hwnd ones as
        # windows_dispatcher_MSG. Accept both.
        if etype == b"windows_dispatcher_MSG" or b"windows" in etype:
            try:
                msg = _MSG.from_address(int(message))
            except Exception:
                return False, 0
            if msg.message == WM_HOTKEY:
                hid = int(msg.wParam)
                if hid in self._callbacks:
                    self.hotkey_activated.emit(hid)
                    return True, 0
            elif msg.message == WM_THEMECHANGED:
                self.theme_changed.emit()
        return False, 0
