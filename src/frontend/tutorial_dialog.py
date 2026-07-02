"""Welcome/tutorial dialog shown on first launch."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.backend.icon import get_app_icon
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.constants import (
    TUTORIAL_DIALOG_DEFAULT,
    TUTORIAL_DIALOG_MIN,
    TUTORIAL_OVERLAP_RADIUS,
    TUTORIAL_MAIN_LAYOUT_MARGINS,
    TUTORIAL_PAGE_MARGINS,
    TUTORIAL_BLOCK_SPACING,
    TUTORIAL_TEXT_OPACITY,
    FONT_SIZE_TITLE_LG,
    SPACING_LG,
    SPACING_MD,
)


class TutorialDialog(GlassPanelDialog):
    _PAGES = [
        [
            ("Add a task", "Type in the input bar and press Enter. Click anywhere else to remove focus from it."),
            ("Auto-scroll", "The list scrolls automatically so your newest task is always visible."),
            ("Edit / Delete", "Double-click a task to edit it, or right-click for more options including Delete."),
            ("Groups", "Use the Group dropdown and + button to organize tasks. Disable groups in Settings → Advanced for a flat list view."),
        ],
        [
            ("Drag to reorder", "Drag a task by its text to reorder it within its group or move it to another group."),
            ("Drag groups", "Drag a group's header to rearrange your task groups. Drop it between other groups — a line shows where it lands."),
            ("Drag text out", "Drag a task's text into Notepad, a browser, or any text field → it pastes as plain text."),
            ("Task reminders", "Right-click a task → Set Reminder. Choose a preset or pick a custom date/time. Supports repeat intervals."),
        ],
        [
            ("Checkboxes", "Each task has a checkbox to mark it complete. Completed tasks move to History."),
            ("Due dates", "Right-click a task → Set Due Date to add a deadline. Due dates show as chips next to the task."),
            ("Priority", "Right-click a task → Set Priority to mark as High priority. High priority tasks show a red indicator."),
            ("Tags", "Right-click a task → Add Tag to organize tasks. Tags appear as colored pills next to the task text. Click a tag pill to change its color."),
        ],
        [
            ("Recurring tasks", "Right-click a task → Set Recurrence to repeat daily, weekly, or monthly. When completed, the task automatically recreates with the next due date."),
            ("Tag filter", "Use the tag filter dropdown in the title bar to show only tasks with specific tags. Filter by multiple tags at once."),
            ("Footer bar", "The footer shows your task count and a shortcut to History for quick access."),
            ("Font selection", "Settings → Appearance → choose a custom font for task text."),
        ],
        [
            ("Timer", "Click the timer icon in the title bar to start a countdown. Double-click a timer to edit its duration."),
            ("History", "Click the clock icon in the footer to restore previously completed tasks. Newly archived tasks appear live while History is open. Use the search bar to filter entries by task text or group name."),
            ("History: Clear All", "In the History panel, click Clear All to remove every archived task at once. History entries are automatically cleaned up based on your retention setting."),
            ("History retention", "Settings → Advanced → choose how long to keep history (5 days to Forever). Older entries are automatically removed on startup."),
        ],
        [
            ("Undo toast", "After deleting a task, a short popup lets you Undo or click ✕ to dismiss it without undoing. The toast auto-closes if you click away."),
            ("Settings", "Click the gear icon to open Settings with tabs: General, Appearance, Keyboard Shortcuts, Export, Reminders, and Advanced. Settings remembers which tab you were on."),
            ("Overflow menu", "Click ··· for quick access to Check for Updates, Send Feedback, and Support Nudge."),
            ("Keyboard shortcuts", "Settings → Keyboard Shortcuts to customize shortcuts for History, Settings, Timer, and more."),
        ],
        [
            ("Themes", "Settings → Appearance → switch between Dark, Light, and OLED themes. Changes apply instantly."),
            ("Mouse glow", "Settings → Appearance → toggle the mouse glow effect. A soft light follows your cursor over the task list."),
            ("Text size", "Settings → Appearance → adjust the Text Size slider to make task text larger or smaller. Changes apply live!"),
            ("Always on Top", "Press Alt+T to keep the window above others."),
        ],
        [
            ("Pin to Desktop", "Ctrl+P pins the window to your desktop so it stays visible behind other windows."),
            ("Export", "Press Ctrl+E or use the Export tab in Settings to export tasks as .txt, .md, or .csv."),
            ("Check for updates", "Settings → General or click 🔄 in the title bar. Downloads run in the background — keep working while it downloads. Choose Install Now or Remind Me Later. Cached downloads skip re-downloading next time."),
            ("Tray icon", "Right-click the tray icon to show the window or quit. The ✖ close button minimizes to tray."),
        ],
        [
            ("Resize", "Drag any edge or corner of the window to resize it."),
            ("Reminders popup", "Press Alt+R to open the Reminders popup showing all pending task reminders. Cancel individual reminders or clear them all."),
            ("Task count", "The footer shows how many active tasks you have at a glance."),
            ("You're all set!", "You're ready to use Nudge! Explore Settings to customize your experience."),
        ],
    ]

    def __init__(self, parent=None):
        super().__init__(parent, overlap_radius=TUTORIAL_OVERLAP_RADIUS, escape_action="accept")
        self._page_index = 0
        self._pages: list[QWidget] = []
        self._prev_btn = None
        self._next_btn = None
        self._page_label = None
        self._stack = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Welcome")
        self.setWindowIcon(get_app_icon())
        self.resize(*TUTORIAL_DIALOG_DEFAULT)
        self.setMinimumSize(*TUTORIAL_DIALOG_MIN)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*TUTORIAL_MAIN_LAYOUT_MARGINS)
        layout.setSpacing(SPACING_LG)

        title = QLabel("Welcome to Nudge!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: {FONT_SIZE_TITLE_LG}px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Your Liquid Glass task widget")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"opacity: {TUTORIAL_TEXT_OPACITY};")
        layout.addWidget(subtitle)

        self._stack = QStackedWidget()
        for page_items in self._PAGES:
            page = QWidget()
            page_lay = QVBoxLayout(page)
            page_lay.setSpacing(SPACING_LG)
            page_lay.setContentsMargins(*TUTORIAL_PAGE_MARGINS)
            for feat_title, feat_desc in page_items:
                block = QVBoxLayout()
                block.setSpacing(TUTORIAL_BLOCK_SPACING)
                t = QLabel(feat_title)
                t.setStyleSheet("font-weight: bold;")
                d = QLabel(feat_desc)
                d.setWordWrap(True)
                d.setStyleSheet(f"opacity: {TUTORIAL_TEXT_OPACITY};")
                block.addWidget(t)
                block.addWidget(d)
                page_lay.addLayout(block)
            page_lay.addStretch()
            self._pages.append(page)
            self._stack.addWidget(page)
        self._stack.setCurrentIndex(0)
        layout.addWidget(self._stack, stretch=1)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(SPACING_MD)
        self._prev_btn = QPushButton("\u25c0 Prev")
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.clicked.connect(self._prev_page)
        self._prev_btn.setEnabled(False)
        nav_row.addWidget(self._prev_btn)

        self._page_label = QLabel()
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_row.addWidget(self._page_label, stretch=1)

        self._next_btn = QPushButton("Next \u25b6")
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self._next_page)
        nav_row.addWidget(self._next_btn)

        layout.addLayout(nav_row)

        got_it = QPushButton("Got it!")
        got_it.setObjectName("primaryButton")
        got_it.setDefault(True)
        got_it.clicked.connect(self.accept)
        layout.addWidget(got_it)

        self._update_nav()

    def _update_nav(self):
        total = len(self._PAGES)
        self._page_label.setText(f"{self._page_index + 1} / {total}")
        self._prev_btn.setEnabled(self._page_index > 0)
        self._next_btn.setVisible(self._page_index < total - 1)

    def _prev_page(self):
        if self._page_index > 0:
            self._page_index -= 1
            self._stack.setCurrentIndex(self._page_index)
            self._update_nav()

    def _next_page(self):
        if self._page_index < len(self._PAGES) - 1:
            self._page_index += 1
            self._stack.setCurrentIndex(self._page_index)
            self._update_nav()
