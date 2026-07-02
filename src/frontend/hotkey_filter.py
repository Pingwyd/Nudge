"""Global hotkey event filter."""

import ctypes
from ctypes import wintypes

from PyQt6.QtCore import QAbstractNativeEventFilter, Qt
from PyQt6.QtGui import QKeySequence

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
    ]


class GlobalHotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self):
        super().__init__()
        self._callbacks = {}
        self._next_id = 1000
        self._hwnd = None

    def set_hwnd(self, hwnd):
        self._hwnd = hwnd

    def register(self, key_sequence_str, callback):
        seq = QKeySequence.fromString(key_sequence_str, QKeySequence.SequenceFormat.PortableText)
        if seq.isEmpty():
            return None
        key = seq[0]
        qt_key = key.key()
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
        vk = qt_key
        hotkey_id = self._next_id
        self._next_id += 1
        hwnd = self._hwnd if self._hwnd else None
        if not ctypes.windll.user32.RegisterHotKey(hwnd, hotkey_id, mod, vk):
            return None
        self._callbacks[hotkey_id] = callback
        return hotkey_id

    def unregister(self, hotkey_id):
        if hotkey_id in self._callbacks:
            hwnd = self._hwnd if self._hwnd else None
            ctypes.windll.user32.UnregisterHotKey(hwnd, hotkey_id)
            del self._callbacks[hotkey_id]

    def unregister_all(self):
        for hid in list(self._callbacks):
            self.unregister(hid)

    def nativeEventFilter(self, eventType, message):
        etype = bytes(eventType)
        if etype == b"windows_dispatcher_MSG" or b"windows" in etype:
            try:
                msg = _MSG.from_address(int(message))
            except Exception:
                return False, 0
            if msg.message == WM_HOTKEY:
                cb = self._callbacks.get(msg.wParam)
                if cb:
                    cb()
                    return True, 0
        return False, 0
