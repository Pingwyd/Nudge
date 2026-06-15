"""
Centralised constants for the Nudge app.

All magic numbers, hardcoded sizes, timer intervals, and layout values
are defined here. Import from this module instead of scattering literals
throughout the codebase.
"""

# ── Window & Dialog Sizes ─────────────────────────────────────────────
# Format: (default_w, default_h, min_w, min_h)

MAIN_WINDOW_DEFAULT = (300, 300)
MAIN_WINDOW_MIN = (280, 280)

HISTORY_DIALOG_DEFAULT = (350, 450)
HISTORY_DIALOG_MIN = (300, 360)

SETTINGS_DIALOG_DEFAULT = (500, 560)
SETTINGS_DIALOG_MIN = (400, 460)

TUTORIAL_DIALOG_DEFAULT = (400, 420)
TUTORIAL_DIALOG_MIN = (340, 360)

REMINDER_DIALOG_DEFAULT = (420, 260)
REMINDER_DIALOG_MIN = (380, 240)

TIMER_DIALOG_DEFAULT = (480, 340)
TIMER_DIALOG_MIN = (400, 280)

TIMER_EDIT_DIALOG_DEFAULT = (320, 200)
TIMER_EDIT_DIALOG_MIN_WIDTH = 280

UPDATE_INFO_DIALOG_DEFAULT = (420, 480)
UPDATE_INFO_DIALOG_MIN = (320, 360)

DOWNLOAD_DIALOG_DEFAULT = (380, 180)
DOWNLOAD_DIALOG_MIN = (300, 160)

EXPORT_DIALOG_DEFAULT = (380, 420)
EXPORT_DIALOG_MIN = (320, 360)

CRASH_DIALOG_MIN = (500, 350)

WHATS_NEW_DIALOG_DEFAULT = (400, 380)
WHATS_NEW_DIALOG_MIN = (320, 300)

SUPPORT_DIALOG_DEFAULT = (340, 260)
SUPPORT_DIALOG_MIN = (280, 220)

FEEDBACK_DIALOG_DEFAULT = (560, 460)
FEEDBACK_DIALOG_MIN = (420, 380)

MESSAGE_DIALOG_DEFAULT = (350, 150)
MESSAGE_DIALOG_MIN_WIDTH = 360

# ── Widget Sizes ──────────────────────────────────────────────────────

CHROME_BUTTON_SIZE = 28
HISTORY_ICON_SIZE = (16, 16)
HISTORY_BUTTON_SIZE = (28, 28)  # width, height for the 🕒 button

# Button heights
BTN_HEIGHT_SM = 26
BTN_HEIGHT_MD = 28
BTN_HEIGHT_LG = 32

# Button min widths
BTN_MIN_WIDTH_SM = 44
BTN_MIN_WIDTH_MD = 70
BTN_MIN_WIDTH_LG = 80
BTN_MIN_WIDTH_XL = 100

# Sidebar
SIDEBAR_BTN_HEIGHT = 32

# Progress bar
PROGRESS_BAR_HEIGHT = 22

# Drop indicator
DROP_INDICATOR_HEIGHT = 3

# Key sequence edit
KEY_SEQ_EDIT_WIDTH = 120

# Scroll areas
SCROLL_AREA_MIN_HEIGHT = 36
SCROLL_AREA_MAX_HEIGHT = 120

# ── Timer & Delay Intervals (ms) ──────────────────────────────────────

DEFERRED_UPDATE_CHECK_MS = 3000
TASK_REMINDER_CHECK_MS = 15_000
DEFERRED_WHATS_NEW_MS = 1000
TRAY_NOTIFICATION_COOLDOWN_MS = 10_000
RESIZE_DEBOUNCE_MS = 100
ESCAPE_DOUBLE_TAP_MS = 500
COPIED_LABEL_RESET_MS = 1200
TRAY_MESSAGE_DURATION_MS = 3000

# ── Slider Ranges ─────────────────────────────────────────────────────

OPACITY_SLIDER_MIN = 50       # %
OPACITY_SLIDER_MAX = 100      # %
OPACITY_FLOOR = 0.30          # minimum window opacity (float)
OPACITY_DIVISOR = 100.0       # slider → float conversion

TEXT_SIZE_SLIDER_MIN = 16
TEXT_SIZE_SLIDER_MAX = 25

# ── Font Sizes (px) ───────────────────────────────────────────────────

FONT_SIZE_HINT = 10
FONT_SIZE_LABEL_SM = 11
FONT_SIZE_LABEL_MD = 12
FONT_SIZE_BODY = 13
FONT_SIZE_TITLE_SM = 13
FONT_SIZE_TITLE_MD = 14
FONT_SIZE_TITLE_LG = 16

# ── Layout Margins & Spacing ──────────────────────────────────────────

MARGIN紧凑 = (6, 4, 6, 4)       # compact — history rows, task rows
MARGIN_STANDARD = (18, 18, 18, 18)  # standard dialogs
MARGIN_WIDE = (20, 18, 20, 18)      # themed message, export, feedback
MARGIN_SETTINGS_TAB = (6, 8, 6, 6)  # settings tab content

SPACING紧凑 = 4
SPACING_SM = 6
SPACING_MD = 8
SPACING_LG = 10

# ── Border Radius (px) ────────────────────────────────────────────────
# NOTE: These should match theme.py radii dict. Listed here for
# inline stylesheet use where theme access isn't available.

RADIUS_WINDOW = 20
RADIUS_PANEL = 20
RADIUS_INPUT = 10
RADIUS_BUTTON = 8
RADIUS_TAB = 8
RADIUS_CHECKBOX = 4
RADIUS_MENU = 5
RADIUS_SMALL = 4

# ── Misc Widget Sizing ────────────────────────────────────────────────

DURATION_INPUT_MIN_WIDTH = 180
DURATION_APPLY_BTN_WIDTH = 50
DATE_EDIT_MIN_WIDTH = 130
TIME_EDIT_MIN_WIDTH = 90
REPEAT_SPIN_WIDTH = 90
EXPORT_COMBO_HEIGHT = 26
EXPORT_GROUP_SCROLL_MIN = 36
ADD_GROUP_BTN_SIZE = (32, 28)

# Text truncation
REMINDER_LIST_TEXT_MAX = 60     # max chars in reminder list task name

# Context menu
CONTEXT_MENU_X_OFFSET = -80
DIALOG_PLACEMENT_GAP = 15

# ── Download / Network ────────────────────────────────────────────────

DOWNLOAD_CHUNK_SIZE = 65536
URL_FETCH_TIMEOUT_S = 10
POWERSHELL_DOWNLOAD_TIMEOUT_S = 120
MB_DIVISOR = 1024 * 1024

# ── Tray ──────────────────────────────────────────────────────────────

TRAY_EDGE_PADDING = 4

# ── History Icon Rendering ────────────────────────────────────────────

HISTORY_ICON_CANVAS = 16
HISTORY_ICON_FONT_PAD = 6
HISTORY_ICON_FONT_MIN = 10

# ── Hotkey Filter ─────────────────────────────────────────────────────

HOTKEY_START_ID = 1000

# ── Responsive Text ───────────────────────────────────────────────────

RESPONSIVE_TEXT_MIN_COL = 100
RESPONSIVE_TEXT_PCT = 0.4
RESPONSIVE_TEXT_VPAD = 14
RESPONSIVE_TEXT_LABEL_PAD = 5
RESPONSIVE_TEXT_STACK_MIN = 10
