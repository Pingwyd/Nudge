"""Pin/unpin window to desktop and prevent minimize when pinned. Windows: Win32 API. macOS/Linux: no-op."""

import sys

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes, CFUNCTYPE, POINTER, c_ssize_t

    HWND_BOTTOM = 1
    HWND_NOTOPMOST = -2
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOACTIVATE = 0x0010
    GWL_WNDPROC = -4
    WM_SIZE = 0x0005
    SIZE_MINIMIZED = 1
    SWP_FRAMECHANGED = 0x0020

    WNDPROC = CFUNCTYPE(c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

    _original_wndprocs = {}
    _pinned_hwnds = set()
    _minimize_allowed = set()

    def allow_next_minimize(hwnd):
        """Temporarily allow one minimize (for the app's own minimize button)."""
        _minimize_allowed.add(hwnd)

    def _wndproc_callback(hwnd, msg, wparam, lparam):
        if msg == WM_SIZE and wparam == SIZE_MINIMIZED:
            if hwnd in _pinned_hwnds:
                if hwnd in _minimize_allowed:
                    _minimize_allowed.discard(hwnd)
                else:
                    return 0
        orig = _original_wndprocs.get(hwnd)
        if orig:
            return orig(hwnd, msg, wparam, lparam)
        return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    _cb = WNDPROC(_wndproc_callback)

    def pin_to_desktop(hwnd):
        user32 = ctypes.windll.user32
        user32.SetWindowLongPtrW.restype = c_ssize_t
        _pinned_hwnds.add(hwnd)
        orig_addr = user32.SetWindowLongPtrW(hwnd, GWL_WNDPROC, _cb)
        if orig_addr:
            _original_wndprocs[hwnd] = WNDPROC(orig_addr)
        user32.SetWindowPos(
            hwnd, HWND_BOTTOM, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
        )

    def unpin_from_desktop(hwnd):
        user32 = ctypes.windll.user32
        user32.SetWindowLongPtrW.restype = c_ssize_t
        _pinned_hwnds.discard(hwnd)
        orig = _original_wndprocs.pop(hwnd, None)
        if orig:
            user32.SetWindowLongPtrW(hwnd, GWL_WNDPROC, orig)
        user32.SetWindowPos(
            hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
        )
else:
    def allow_next_minimize(hwnd):
        pass

    def pin_to_desktop(hwnd):
        pass

    def unpin_from_desktop(hwnd):
        pass

    def unpin_from_desktop(hwnd):
        pass
