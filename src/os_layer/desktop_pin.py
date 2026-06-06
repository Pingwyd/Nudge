import ctypes
from ctypes import wintypes

# Win32 Constants
HWND_BOTTOM = 1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
GWL_HWNDPARENT = -8

def pin_to_desktop(hwnd):
    """
    Sends the window safely to the bottom-most graphical layer.
    Using SetParent(WorkerW) often breaks transparent window compositing on newer Windows 11 builds, rendering them invisible.
    This pushes it below all apps, acting safely as a desktop widget.
    """
    user32 = ctypes.windll.user32
    
    # Push the window to the bottom Z-order natively
    user32.SetWindowPos(
        hwnd, 
        HWND_BOTTOM, 
        0, 0, 0, 0, 
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
    )

def unpin_from_desktop(hwnd):
    """
    Restores the normal Z-order behavior.
    """
    user32 = ctypes.windll.user32
    user32.SetWindowPos(
        hwnd, 
        HWND_NOTOPMOST, 
        0, 0, 0, 0, 
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
    )
