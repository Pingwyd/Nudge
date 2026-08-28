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
    SWP_FRAMECHANGED = 0x0020
    SW_SHOWNOACTIVATE = 4
    GWL_WNDPROC = -4
    GWL_STYLE = -16
    GWLP_HWNDPARENT = -8
    WS_MINIMIZEBOX = 0x00020000
    WM_SIZE = 0x0005
    WM_SYSCOMMAND = 0x0112
    WM_WINDOWPOSCHANGING = 0x0046
    WM_WINDOWPOSCHANGED = 0x0047
    SIZE_MINIMIZED = 1
    SC_MINIMIZE = 0xF020

    # The shell hides windows during "Show Desktop" (Win+D) by moving them to
    # this off-screen origin rather than issuing a normal minimize. Detecting
    # this in WM_WINDOWPOSCHANGING lets us veto the move before it happens.
    SHOW_DESKTOP_OFFSCREEN = -32000

    WNDPROC = CFUNCTYPE(c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    WNDENUMPROC = CFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    class WINDOWPOS(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("hwndInsertAfter", wintypes.HWND),
            ("x", ctypes.c_int),
            ("y", ctypes.c_int),
            ("cx", ctypes.c_int),
            ("cy", ctypes.c_int),
            ("flags", ctypes.c_uint),
        ]

    _original_wndprocs = {}
    _pinned_hwnds = set()
    _minimize_allowed = set()
    _previous_owners = {}
    _enum_callback_ref = None  # keep alive across EnumWindows

    def _as_hwnd(hwnd):
        return int(hwnd) if hwnd else 0

    def _user32():
        user32 = ctypes.windll.user32
        user32.SetWindowLongPtrW.restype = c_ssize_t
        user32.GetWindowLongPtrW.restype = c_ssize_t
        user32.IsWindow.argtypes = [wintypes.HWND]
        user32.IsWindow.restype = wintypes.BOOL
        return user32

    def _purge_dead_hwnds():
        user32 = _user32()
        for h in list(_pinned_hwnds):
            if not user32.IsWindow(h):
                _pinned_hwnds.discard(h)
                _original_wndprocs.pop(h, None)
                _previous_owners.pop(h, None)
                _minimize_allowed.discard(h)

    def _find_shelldll_defview():
        """Locate SHELLDLL_DefView (desktop icon host) under Progman or WorkerW."""
        user32 = _user32()
        progman = user32.FindWindowW("Progman", None)
        if progman:
            defview = user32.FindWindowExW(progman, None, "SHELLDLL_DefView", None)
            if defview:
                return int(defview)

        found = []

        def _enum(hwnd, _lparam):
            defview = user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None)
            if defview:
                found.append(int(defview))
                return False
            return True

        global _enum_callback_ref
        _enum_callback_ref = WNDENUMPROC(_enum)
        user32.EnumWindows(_enum_callback_ref, 0)
        return found[0] if found else 0

    def _attach_desktop_owner(hwnd):
        """Own the window by the desktop view so Show Desktop leaves it alone."""
        user32 = _user32()
        desktop = _find_shelldll_defview()
        if not desktop:
            return
        if hwnd not in _previous_owners:
            _previous_owners[hwnd] = user32.GetWindowLongPtrW(hwnd, GWLP_HWNDPARENT)
        user32.SetWindowLongPtrW(hwnd, GWLP_HWNDPARENT, desktop)

    def _restore_desktop_owner(hwnd):
        user32 = _user32()
        if hwnd not in _previous_owners:
            return
        prev = _previous_owners.pop(hwnd)
        if user32.IsWindow(hwnd):
            user32.SetWindowLongPtrW(hwnd, GWLP_HWNDPARENT, prev or 0)

    def _keep_visible(hwnd):
        """Undo a Show-Desktop hide/minimize without activating the window."""
        user32 = _user32()
        user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
        user32.SetWindowPos(
            hwnd, HWND_BOTTOM, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
        )

    def allow_next_minimize(hwnd):
        """Temporarily allow one minimize (for the app's own minimize button)."""
        _minimize_allowed.add(_as_hwnd(hwnd))

    def _is_show_desktop_move(pos):
        # Show Desktop slides windows to ~(-32000,-32000). Do NOT treat
        # SWP_HIDEWINDOW as Show Desktop — that breaks intentional hide-to-tray.
        return pos.x <= SHOW_DESKTOP_OFFSCREEN or pos.y <= SHOW_DESKTOP_OFFSCREEN

    def _wndproc_callback(hwnd, msg, wparam, lparam):
        hwnd_i = _as_hwnd(hwnd)
        if hwnd_i in _pinned_hwnds:
            # Block "Show Desktop" (Win+D / Show Desktop button). The shell
            # slides the window off-screen; strip the move so it stays put.
            if msg == WM_WINDOWPOSCHANGING and hwnd_i not in _minimize_allowed:
                pos = ctypes.cast(lparam, POINTER(WINDOWPOS)).contents
                if _is_show_desktop_move(pos):
                    pos.flags |= SWP_NOMOVE | SWP_NOSIZE
                    pos.hwndInsertAfter = wintypes.HWND(HWND_BOTTOM)
                    return 0
            if msg == WM_SYSCOMMAND and (int(wparam) & 0xFFF0) == SC_MINIMIZE:
                if hwnd_i in _minimize_allowed:
                    _minimize_allowed.discard(hwnd_i)
                else:
                    return 0
            if msg == WM_SIZE and wparam == SIZE_MINIMIZED:
                if hwnd_i in _minimize_allowed:
                    _minimize_allowed.discard(hwnd_i)
                else:
                    _keep_visible(hwnd_i)
                    return 0
            if msg == WM_WINDOWPOSCHANGED and hwnd_i not in _minimize_allowed:
                pos = ctypes.cast(lparam, POINTER(WINDOWPOS)).contents
                if _is_show_desktop_move(pos):
                    _keep_visible(hwnd_i)
                    return 0
        orig = _original_wndprocs.get(hwnd_i)
        if orig:
            return orig(hwnd, msg, wparam, lparam)
        return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    _cb = WNDPROC(_wndproc_callback)

    def pin_to_desktop(hwnd):
        user32 = _user32()
        hwnd = _as_hwnd(hwnd)
        if not hwnd or not user32.IsWindow(hwnd):
            return

        _purge_dead_hwnds()

        # HWND may have been recreated by setWindowFlags — drop stale pins.
        for old in list(_pinned_hwnds):
            if old != hwnd:
                _restore_wndproc(old)
                _restore_desktop_owner(old)
                _pinned_hwnds.discard(old)
                _minimize_allowed.discard(old)

        _pinned_hwnds.add(hwnd)

        # A frameless window (no WS_MINIMIZEBOX) may not receive the -32000
        # WM_WINDOWPOSCHANGING on Win+D, so add the style back while pinned.
        style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
        if style and not (style & WS_MINIMIZEBOX):
            user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style | WS_MINIMIZEBOX)

        if hwnd not in _original_wndprocs:
            orig_addr = user32.SetWindowLongPtrW(hwnd, GWL_WNDPROC, _cb)
            if orig_addr:
                _original_wndprocs[hwnd] = WNDPROC(orig_addr)

        _attach_desktop_owner(hwnd)
        user32.SetWindowPos(
            hwnd, HWND_BOTTOM, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
        )

    def _restore_wndproc(hwnd):
        user32 = _user32()
        orig = _original_wndprocs.pop(hwnd, None)
        if orig and user32.IsWindow(hwnd):
            user32.SetWindowLongPtrW(hwnd, GWL_WNDPROC, orig)

    def unpin_from_desktop(hwnd):
        user32 = _user32()
        hwnd = _as_hwnd(hwnd)
        _purge_dead_hwnds()

        targets = set(_pinned_hwnds)
        if hwnd:
            targets.add(hwnd)

        for h in targets:
            _pinned_hwnds.discard(h)
            _minimize_allowed.discard(h)
            _restore_wndproc(h)
            _restore_desktop_owner(h)
            if user32.IsWindow(h):
                user32.SetWindowPos(
                    h, HWND_NOTOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
                )
else:
    def allow_next_minimize(hwnd):
        pass

    def pin_to_desktop(hwnd):
        pass

    def unpin_from_desktop(hwnd):
        pass
