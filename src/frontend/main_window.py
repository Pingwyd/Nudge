import threading
from datetime import datetime, timedelta

from PyQt6.QtCore import (QAbstractNativeEventFilter, QByteArray, QEvent,
                           QMimeData, QPoint, QPointF, QRect, QSize, Qt,
                           QTimer, pyqtSignal)
from PyQt6.QtGui import (QAction, QBrush, QColor, QCursor, QDrag, QFont, QIcon,
                         QKeySequence, QPainter, QPixmap, QRadialGradient,
                         QShortcut)
from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateEdit,
                             QDialog, QFrame, QGraphicsDropShadowEffect,
                             QHBoxLayout, QKeySequenceEdit,
                             QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QMainWindow, QMenu, QMessageBox, QPushButton,
                             QScrollArea, QSizePolicy, QSlider, QSpinBox,
                             QStackedWidget, QTimeEdit, QVBoxLayout, QWidget)

from src import __version__
from src.backend.boot_checker import BootChecker
from src.backend.group_store import GroupStore
from src.backend.icon import get_app_icon
from src.backend.input_parser import InputParser
from src.backend.state_manager import StateManager
from src.backend.task_groups import (GENERAL_GROUP_ID, create_group,
                                     group_by_id, group_name,
                                     migrate_tasks_group_ids,
                                     rebuild_tasks_preserving_groups,
                                     sorted_groups, tasks_for_group)
from src.backend.task_store import TaskStore
from src.backend.updater import (UpdateCheckResult, check_for_update,
                                 parse_changelog)
from src.backend.window_geometry import (DEFAULT_WINDOW_HEIGHT,
                                         DEFAULT_WINDOW_WIDTH,
                                         MIN_WINDOW_HEIGHT, MIN_WINDOW_WIDTH)
from src.backend.window_layer import (compose_main_window_flags,
                                      reconcile_layer_settings)
from src.frontend.feedback_dialog import FeedbackDialog
from src.frontend.frameless_chrome import FramelessChromeController
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.history_row import HistoryRowWidget
from src.frontend.responsive_text import (ResponsiveTextRowHelper,
                                          apply_editor_field_width,
                                          fix_single_line_editor_height,
                                          label_content_height,
                                          sync_stacked_page_height)
from src.frontend.task_group_section import TaskGroupSection
from src.frontend.theme import (apply_theme_to_app, generate_svg_icon,
                                get_icon_color, get_theme, menu_stylesheet,
                                normalize_theme_id, refresh_glass_shells,
                                svg_to_pixmap)
from src.frontend.themed_input_dialog import ThemedInputDialog
from src.frontend.themed_message_dialog import ThemedMessageDialog
from src.frontend.update_dialog import UpdateInfoDialog
from src.os_layer.desktop_pin import pin_to_desktop, unpin_from_desktop
from src.os_layer.platform_utils import open_url
from src.os_layer.system_tray import SystemTrayManager


def set_label_point_size(label, point_size, bold=False):
    font = label.font()
    font.setPointSize(point_size)
    font.setBold(bold)
    label.setFont(font)


class GlowOverlay(QWidget):
    """Transparent overlay that paints a glass shine following the mouse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._center = QPointF(-9999, -9999)
        self._radius = 200
        self._visible = False

    def set_glow_center(self, point: QPointF):
        self._center = point
        self._visible = True
        self.update()

    def hide_glow(self):
        self._visible = False
        self._center = QPointF(-9999, -9999)
        self.update()

    def paintEvent(self, event):
        if not self._visible:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Inner core — bright, tight
        inner = QRadialGradient(self._center, self._radius * 0.35)
        inner.setColorAt(0, QColor(255, 255, 255, 25))
        inner.setColorAt(0.6, QColor(255, 255, 255, 8))
        inner.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(inner))
        painter.drawEllipse(self._center, self._radius * 0.35, self._radius * 0.35)

        # Outer halo — soft, wide
        outer = QRadialGradient(self._center, self._radius)
        outer.setColorAt(0, QColor(255, 255, 255, 12))
        outer.setColorAt(0.5, QColor(255, 255, 255, 4))
        outer.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(outer))
        painter.drawEllipse(self._center, self._radius, self._radius)

        painter.end()


# --- Global hotkey support (Win32 RegisterHotKey) ---
import ctypes
from ctypes import wintypes

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



class TaskRowWidget(QWidget):
    """One task row: compact height, scroll area absorbs extra space — not individual rows."""

    def __init__(
        self,
        text,
        checked=False,
        text_size=14,
        on_toggled=None,
        on_commit=None,
        on_context_menu=None,
        content_indent=0,
        parent=None,
    ):
        super().__init__(parent)
        self.on_toggled = on_toggled
        self.on_commit = on_commit
        self.on_context_menu = on_context_menu
        self._editing = False
        self._indent_spacer = None
        self._main_window = None
        self._task_ref = None
        self._drag_start_pos = None
        self.setToolTip("Double-click to complete")

        # Horizontal fill only; vertical size comes from content, not leftover list height.
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 0, 2)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if content_indent > 0:
            self._indent_spacer = QWidget()
            self._indent_spacer.setFixedWidth(content_indent)
            self._indent_spacer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            layout.addWidget(self._indent_spacer)

        self.content_stack = QStackedWidget()
        # Height is set in _sync_content_stack_height() to match the visible page only.
        self.content_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        display_page = QWidget()
        display_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        display_layout = QHBoxLayout(display_page)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(0)

        self.label = QLabel(text)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        display_layout.addWidget(self.label, 1)

        edit_page = QWidget()
        edit_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        edit_layout = QHBoxLayout(edit_page)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        edit_layout.setSpacing(0)

        self.editor = QLineEdit(text)
        self.editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.editor.returnPressed.connect(self.commit_edit)
        self.editor.setDragEnabled(True)
        edit_layout.addWidget(self.editor, 1)

        self.content_stack.addWidget(display_page)
        self.content_stack.addWidget(edit_page)
        layout.addWidget(self.content_stack, 1, Qt.AlignmentFlag.AlignVCenter)

        self._countdown_label = QLabel()
        self._countdown_label.setStyleSheet("font-size: 10px;color: transparent; background: transparent; border: none;")
        self._countdown_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._countdown_label.setFixedHeight(14)
        self._countdown_label.hide()

        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._update_countdown)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setObjectName("ghostButton")
        self.edit_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.edit_btn.setStyleSheet("font-size: 12px; padding: 3px 10px; min-height: 0;")
        self.edit_btn.clicked.connect(self.toggle_edit_mode)

        self._edit_column = QVBoxLayout()
        self._edit_column.setContentsMargins(0, 0, 0, 0)
        self._edit_column.setSpacing(0)
        self._edit_column.addWidget(self._countdown_label, 0, Qt.AlignmentFlag.AlignRight)
        self._edit_column.addWidget(self.edit_btn, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(self._edit_column, 0)

        reserved = [self.edit_btn]
        if self._indent_spacer is not None:
            reserved.insert(0, self._indent_spacer)
        self._text_layout = ResponsiveTextRowHelper(
            self, self.label, reserved, editor=self.editor
        )
        self._text_layout.set_content_stack(self.content_stack)
        self.set_text_size(text_size)
        QTimer.singleShot(0, self.sync_text_layout)

    def _handle_toggled(self, checked):
        if self.on_toggled:
            self.on_toggled(checked)

    def set_text_size(self, text_size):
        font = self.label.font()
        font.setPixelSize(text_size)
        self.label.setFont(font)
        self.label.setStyleSheet(f"font-size: {int(text_size)}px;")
        editor_font = self.editor.font()
        editor_font.setPixelSize(text_size)
        self.editor.setFont(editor_font)
        self.editor.setStyleSheet(f"font-size: {int(text_size)}px;")
        side_h = max(18, int(text_size) + 4)
        self.edit_btn.setFixedHeight(side_h)
        self.edit_btn.setStyleSheet(
            f"font-size: {max(11, int(text_size) - 2)}px; padding: 2px 10px; min-height: 0;"
        )
        self.sync_text_layout()

    def sync_text_layout(self):
        self._text_layout.sync_layout()
        self._sync_content_stack_height()

    def _sync_content_stack_height(self):
        """Content stack height accounts for full wrapped text height."""
        column_width = max(1, self.content_stack.width())
        if self._editing:
            apply_editor_field_width(self.editor, column_width)
            fix_single_line_editor_height(self.editor)
            sync_stacked_page_height(self.content_stack, self.editor.height())
        else:
            label_height = label_content_height(self.label, column_width)
            sync_stacked_page_height(self.content_stack, label_height + 2)

    def begin_edit(self):
        if self._editing:
            return
        self._editing = True
        self.editor.setText(self.label.text())
        self.content_stack.setCurrentIndex(1)
        self.edit_btn.setText("Save")
        self.content_stack.updateGeometry()
        self.updateGeometry()
        self.sync_text_layout()
        QTimer.singleShot(0, lambda: (
            self.editor.setFocus(),
            self.editor.selectAll()
        ))

    def commit_edit(self):
        if not self._editing:
            self.begin_edit()
            return

        new_text = self.editor.text().strip()
        if not new_text:
            self.editor.setFocus()
            self.editor.selectAll()
            return

        self.label.setText(new_text)
        self._editing = False
        self.content_stack.setCurrentIndex(0)
        self.edit_btn.setText("Edit")
        self.content_stack.updateGeometry()
        self.updateGeometry()
        if self.on_commit:
            self.on_commit(new_text)
        self.sync_text_layout()

    def toggle_edit_mode(self):
        if self._editing:
            self.commit_edit()
        else:
            self.begin_edit()

    def set_task_ref(self, task_ref):
        self._task_ref = task_ref
        has_reminder = False
        if self._main_window is not None and hasattr(self._main_window, '_timer_manager'):
            cfg = self._main_window._timer_manager.get_timer_for_task(task_ref["id"])
            if cfg is not None and cfg.enabled:
                has_reminder = True
        if has_reminder:
            self._start_countdown()
        else:
            self._stop_countdown()

    def _start_countdown(self):
        if not self._countdown_timer.isActive():
            self._apply_countdown_theme()
            self._update_countdown()
            self._countdown_timer.start()

    def _stop_countdown(self):
        if self._countdown_timer.isActive():
            self._countdown_timer.stop()
        self._countdown_label.hide()
        self._countdown_label.setStyleSheet("font-size: 10px; color: transparent; background: transparent; border: none;")

    def _update_countdown(self):
        trigger_at = None
        if self._main_window is not None and hasattr(self._main_window, '_timer_manager'):
            cfg = self._main_window._timer_manager.get_timer_for_task(self._task_ref["id"])
            if cfg is not None:
                trigger_at = cfg.next_trigger_at
        if trigger_at is None:
            self._stop_countdown()
            return
        remaining = int(trigger_at - datetime.now().timestamp())
        if remaining <= 0:
            self._stop_countdown()
            return
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        if hours > 0:
            text = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            text = f"{minutes}m {seconds}s"
        else:
            text = f"{seconds}s"
        self._countdown_label.setText(text)
        self._countdown_label.show()

    def _apply_countdown_theme(self):
        parent = self.parent()
        theme_id = "dark"
        if parent and hasattr(parent, "app_state"):
            theme_id = normalize_theme_id(parent.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        accent = theme["colors"].get("accent", "#4fc3f7")
        self._countdown_label.setStyleSheet(
            f"font-size: 10px; color: {accent}; background: transparent; border: none;"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_text_layout()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._task_ref is not None:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (self._drag_start_pos is not None and
            event.buttons() & Qt.MouseButton.LeftButton):
            delta = event.position().toPoint() - self._drag_start_pos
            if delta.manhattanLength() > 10:
                drag = QDrag(self)
                mime = QMimeData()
                mime.setData("application/x-nudge-task-row", QByteArray())
                task_text = self._task_ref.get("text", "") if self._task_ref else ""
                mime.setText(task_text)
                drag.setMimeData(mime)
                pix = self.grab()
                ghost = QPixmap(pix.size())
                ghost.fill(Qt.GlobalColor.transparent)
                p = QPainter(ghost)
                p.setOpacity(0.55)
                p.drawPixmap(0, 0, pix)
                p.end()
                drag.setPixmap(ghost)
                drag.setHotSpot(delta)
                drag.exec(Qt.DropAction.MoveAction)
                self._drag_start_pos = None
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._editing:
            return super().mouseReleaseEvent(event)
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._editing:
            return super().mouseDoubleClickEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_child = self.childAt(event.position().toPoint())
            if clicked_child not in (self.edit_btn, self.editor):
                if self.on_toggled:
                    self.on_toggled(True)
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def contextMenuEventFromChild(self, global_pos):
        if self.on_context_menu:
            self.on_context_menu(global_pos)

    def contextMenuEvent(self, event):
        if self.on_context_menu:
            self.on_context_menu(event.globalPos())
            event.accept()
            return
        super().contextMenuEvent(event)


class UndoToast(QFrame):
    """Non-blocking toast that auto-dismisses after a timeout, with an Undo button."""

    def __init__(self, parent, message, undo_callback, timeout_ms=5000):
        super().__init__(parent)
        self._main_window = parent
        self._undo_callback = undo_callback
        self.setObjectName("undoToast")
        self.setMaximumWidth(600)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        undo_btn = QPushButton("Undo")
        undo_btn.setObjectName("ghostButton")
        undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        undo_btn.clicked.connect(self._on_undo)
        layout.addWidget(undo_btn)

        dismiss_btn = QPushButton("X")
        dismiss_btn.setObjectName("ghostButton")
        dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        font = dismiss_btn.font()
        font.setBold(True)
        dismiss_btn.setFont(font)
        dismiss_btn.clicked.connect(self._dismiss)
        layout.addWidget(dismiss_btn)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(timeout_ms)
        self._timer.timeout.connect(self._dismiss)
        self._timer.start()

    def _on_undo(self):
        if self._undo_callback:
            self._undo_callback()
        self._dismiss()

    def _dismiss(self):
        if self._timer.isActive():
            self._timer.stop()
        self.hide()
        self.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_theme()
        self._reposition()

    def _reposition(self):
        parent = self._main_window
        if parent is None:
            return
        self.adjustSize()
        if self.layout() is not None:
            self.layout().activate()
        tw = self.width()
        th = self.height()
        margin = 10
        pw = parent.width()
        ph = parent.height()
        screen_pos = parent.mapToGlobal(QPoint(0, 0))
        screen = parent.screen().availableGeometry()
        x_right = screen_pos.x() + pw + margin
        if x_right + tw <= screen.right():
            x = x_right
        else:
            x = screen_pos.x() - tw - margin
        if x < screen.left():
            x = screen.left()
        y = screen_pos.y() + ph - th - margin
        if y < screen.top():
            y = screen.top()
        if y + th > screen.bottom():
            y = screen.bottom() - th
        self.move(x, y)

    def _apply_theme(self):
        parent = self._main_window
        theme_id = "dark"
        if parent and hasattr(parent, "app_state"):
            theme_id = normalize_theme_id(parent.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        c = theme["colors"]
        self.setStyleSheet(f"""
            QFrame#undoToast {{
                background: {c.get('glass_start', '#1e1e1e')};
                border: 1px solid {c.get('border', 'rgba(255,255,255,60)')};
                border-radius: 12px;
            }}
            QLabel {{
                color: {c.get('text', '#ffffff')};
                font-size: 13px;
            }}
            QPushButton {{
                color: {c.get('accent', '#4fc3f7')};
                font-weight: bold;
                font-size: 13px;
                border: none;
                background: transparent;
            }}
        """)


class CollapsibleHeader(QWidget):
    def __init__(self, title, count, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._children = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 4)

        self._toggle_btn = QPushButton(f"\u25bc {title} ({count})")
        self._toggle_btn.setObjectName("ghostButton")
        self._toggle_btn.setStyleSheet("text-align: left; font-weight: bold; font-size: 13px;")
        self._toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self._toggle_btn)

    def _toggle(self):
        self._expanded = not self._expanded
        icon = "\u25bc" if self._expanded else "\u25b6"
        text = self._toggle_btn.text()
        self._toggle_btn.setText(f"{icon} {text[2:]}")
        for child in self._children:
            child.setVisible(self._expanded)

    def add_child(self, widget):
        self._children.append(widget)


class HistoryDialog(GlassPanelDialog):
    def __init__(self, history_store, restore_callback, groups_data=None, parent=None, state_manager=None):
        super().__init__(parent, overlap_radius=20, escape_action="close")
        self.history_store = history_store
        self.restore_callback = restore_callback
        self.groups_data = groups_data or {"groups": []}
        self.rows = []
        self._history_tasks = []
        self.title_label = None
        self._chrome = None
        self._state_manager = state_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Task History")
        self.setWindowIcon(get_app_icon())
        if self._state_manager:
            w, h = self._state_manager.get_history_window_size()
        else:
            w, h = 350, 450
        self.resize(w, h)
        self.setMinimumSize(300, 360)
        self.setMouseTracking(True)
        self._chrome = FramelessChromeController(self, min_width=300, min_height=360)

        self.bg_frame.setGeometry(0, 0, 380, 560)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        title = QLabel("Completed Tasks History")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold;")
        self.title_label = title
        layout.addWidget(title)

        hint = QLabel("Double-click any entry to restore it to the task list.")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("opacity: 0.7;")
        layout.addWidget(hint)

        self.skip_delete_cb = QCheckBox("Don't ask for confirmation to delete")
        self.skip_delete_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        if self._state_manager:
            skip = self._state_manager.state.get("historySkipDeleteConfirm", False)
            self.skip_delete_cb.setChecked(skip)
            self.skip_delete_cb.toggled.connect(self._on_skip_delete_toggled)
        layout.addWidget(self.skip_delete_cb)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search history...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self._filter_history)
        layout.addWidget(self.search_bar)

        # Scroll area for tasks matching the main window
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tasks_widget = QWidget()
        self.tasks_widget.setObjectName("transparentSurface")
        self.tasks_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tasks_layout.setSpacing(6)
        
        self.scroll_area.setWidget(self.tasks_widget)
        layout.addWidget(self.scroll_area, stretch=1)
        
        self.refresh_history()
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.setObjectName("ghostButton")
        clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_all_btn.clicked.connect(self.clear_all_history)
        layout.addWidget(clear_all_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_history_row_text_layouts()
        if self._state_manager and event.oldSize().isValid():
            self._state_manager.save_history_window_size(event.size().width(), event.size().height())

    def _get_theme_id(self):
        parent = self.parent()
        if parent is not None and hasattr(parent, "app_state"):
            return normalize_theme_id(parent.app_state.get("theme", "dark"))
        return "dark"

    def _filter_history(self, text):
        query = text.strip().lower()
        for row in self.rows:
            task_text = row.task_ref.get("text", "").lower()
            row.setVisible(not query or query in task_text)
        for i in range(self.tasks_layout.count()):
            widget = self.tasks_layout.itemAt(i).widget()
            if isinstance(widget, CollapsibleHeader):
                any_visible = any(child.isVisible() for child in widget._children)
                widget.setVisible(any_visible)

    def _sync_history_row_text_layouts(self):
        for row in self.rows:
            if hasattr(row, "sync_text_layout"):
                row.sync_text_layout()

    def _group_by_time_period(self, entries):
        from datetime import datetime, timedelta
        now = datetime.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        groups = {"Today": [], "Yesterday": [], "This Week": [], "Older": []}
        for entry in entries:
            try:
                completed_at = datetime.fromisoformat(entry.get("completedAt", ""))
                entry_date = completed_at.date()
            except (ValueError, TypeError):
                groups["Older"].append(entry)
                continue
            if entry_date == today:
                groups["Today"].append(entry)
            elif entry_date == yesterday:
                groups["Yesterday"].append(entry)
            elif entry_date >= week_ago:
                groups["This Week"].append(entry)
            else:
                groups["Older"].append(entry)
        return groups

    def refresh_history(self):
        self.rows.clear()
        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._history_tasks = self.history_store.load()
        count = len(self._history_tasks)
        self.title_label.setText(f"Completed Tasks History ({count})")

        filtered = self._get_filtered_entries(self._history_tasks) if hasattr(self, '_get_filtered_entries') else self._history_tasks
        groups = self._group_by_time_period(filtered)

        for period_name, period_entries in groups.items():
            if not period_entries:
                continue
            header = CollapsibleHeader(period_name, len(period_entries))
            self.tasks_layout.addWidget(header, 0, Qt.AlignmentFlag.AlignTop)
            for task in period_entries:
                gname = group_name(self.groups_data, task.get("groupId"))
                display_text = f"[{gname}] {task.get('text', '')}"
                row = HistoryRowWidget(
                    display_text,
                    text_size=14,
                    on_restore=lambda t=task: self.restore_history_item(t),
                    on_delete=lambda t=task: self.delete_history_item(t),
                )
                row.task_ref = task
                self.tasks_layout.addWidget(row, 0, Qt.AlignmentFlag.AlignTop)
                self.rows.append(row)
                header.add_child(row)

        self.tasks_layout.addStretch(1)
        QTimer.singleShot(0, self._sync_history_row_text_layouts)
        self.tasks_widget.setUpdatesEnabled(True)

    def add_external_archived_task(self, archived_task):
        """Append a row for a task archived from the main window while dialog is open."""
        self._history_tasks.append(archived_task)
        date_str = archived_task.get("completedAt", "").split("T")[0]
        gname = group_name(self.groups_data, archived_task.get("groupId"))
        display_text = f"[{date_str}] [{gname}] {archived_task.get('text', '')}"
        row = HistoryRowWidget(
            display_text,
            text_size=14,
            on_restore=lambda t=archived_task: self.restore_history_item(t),
            on_delete=lambda t=archived_task: self.delete_history_item(t),
        )
        row.task_ref = archived_task
        self.tasks_layout.insertWidget(0, row, 0, Qt.AlignmentFlag.AlignTop)
        self.rows.insert(0, row)
        self._filter_history(self.search_bar.text())
        QTimer.singleShot(0, self._sync_history_row_text_layouts)

    def restore_history_item(self, task_ref):
        self.restore_callback(task_ref)
        self._remove_row_for_task(task_ref)
        self._history_tasks = [t for t in self._history_tasks if t is not task_ref]
        self.history_store.save(self._history_tasks)

    def _on_skip_delete_toggled(self, checked):
        if self._state_manager:
            self._state_manager.state["historySkipDeleteConfirm"] = checked
            self._state_manager.save()

    def delete_history_item(self, task_ref):
        skip_confirm = self._state_manager.state.get("historySkipDeleteConfirm", False) if self._state_manager else False
        if not skip_confirm:
            if not ThemedMessageDialog.question(self, "Delete History Entry", "Are you sure you want to delete this history entry? This cannot be undone."):
                return
        self._remove_row_for_task(task_ref)
        self._history_tasks = [t for t in self._history_tasks if t is not task_ref]
        self.history_store.save(self._history_tasks)

    def _remove_row_for_task(self, task_ref):
        for row in list(self.rows):
            if row.task_ref is task_ref:
                self.tasks_layout.removeWidget(row)
                row.deleteLater()
                self.rows.remove(row)
                break
        QTimer.singleShot(0, self._sync_history_row_text_layouts)

    def clear_all_history(self):
        skip_confirm = self._state_manager.state.get("historySkipDeleteConfirm", False) if self._state_manager else False
        if not skip_confirm:
            if not ThemedMessageDialog.question(self, "Clear History", "Are you sure you want to clear ALL history entries? This cannot be undone."):
                return
        self.rows.clear()
        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._history_tasks = []
        self.history_store.save(self._history_tasks)
        if self.title_label:
            self.title_label.setText("Completed Tasks History (0)")
        self.tasks_layout.addStretch(1)
        self._sync_history_row_text_layouts()

class TutorialDialog(GlassPanelDialog):
    _PAGES = [
        [
            ("Add a task", "Type in the input bar and press Enter. Click anywhere else to remove focus from it."),
            ("Auto-scroll", "The list scrolls automatically so your newest task is always visible."),
            ("Edit / Delete", "Right-click a task or use the Edit button on its right edge."),
            ("Groups", "Use the Group dropdown and + button to organize tasks. Disable groups in Settings → Advanced for a flat list view."),
        ],
        [
            ("Drag to reorder", "Drag a task by its text to reorder it within its group or move it to another group."),
            ("Drag groups", "Drag a group's header to rearrange your task groups. Drop it between other groups — a line shows where it lands."),
            ("Drag text out", "Drag a task's text into Notepad, a browser, or any text field → it pastes as plain text."),
            ("Task reminders", "Right-click a task → Set Reminder. Choose a preset or pick a custom date/time. Supports repeat intervals."),
        ],
        [
            ("Timer", "Click the timer icon in the title bar to start a countdown. Double-click a timer to edit its duration."),
            ("History", "Click the clock icon to restore previously completed tasks. Newly archived tasks appear live while History is open. Use the search bar to filter entries."),
            ("History: Clear All", "In the History panel, click Clear All to remove every archived task at once. Toggle 'Don't ask to delete' to skip confirmation."),
            ("Undo toast", "After deleting a task, a short popup lets you Undo or click ✕ to dismiss it without undoing."),
        ],
        [
            ("Settings", "Click the gear icon to open Settings with 6 tabs: General, Appearance, Keyboard Shortcuts, Export, Reminders, and Advanced."),
            ("Overflow menu", "Click ··· for quick access to Check for Updates, Send Feedback, and Support Nudge."),
            ("Keyboard shortcuts", "Settings → Keyboard Shortcuts to customize shortcuts for History, Settings, Timer, and more."),
            ("Text size", "Settings → Appearance → adjust the Text Size slider to make task text larger or smaller. Changes apply live!"),
        ],
        [
            ("Themes", "Settings → Appearance → switch between Dark, Light, and OLED themes. Changes apply instantly."),
            ("Mouse glow", "Settings → Appearance → toggle the mouse glow effect. A soft light follows your cursor over the task list."),
            ("Always on Top", "Press Alt+T to keep the window above others."),
            ("Pin to Desktop", "Alt+P pins the window to your desktop so it stays visible behind other windows."),
        ],
        [
            ("Export", "Press Ctrl+E or use the Export tab in Settings to export tasks as .txt, .md, or .csv."),
            ("Check for updates", "Settings → General or click 🔄 in the title bar to check for new versions."),
            ("Tray icon", "Right-click the tray icon to show the window or quit. The ✖ close button minimizes to tray."),
            ("Resize", "Drag any edge or corner of the window."),
        ],
    ]

    def __init__(self, parent=None):
        super().__init__(parent, overlap_radius=20, escape_action="accept")
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
        self.resize(400, 420)
        self.setMinimumSize(340, 360)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel("Welcome to Nudge!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Your Liquid Glass task widget")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("opacity: 0.7;")
        layout.addWidget(subtitle)

        self._stack = QStackedWidget()
        for page_items in self._PAGES:
            page = QWidget()
            page_lay = QVBoxLayout(page)
            page_lay.setSpacing(10)
            page_lay.setContentsMargins(5, 5, 5, 5)
            for feat_title, feat_desc in page_items:
                block = QVBoxLayout()
                block.setSpacing(2)
                t = QLabel(feat_title)
                t.setStyleSheet("font-weight: bold;")
                d = QLabel(feat_desc)
                d.setWordWrap(True)
                d.setStyleSheet("opacity: 0.7;")
                block.addWidget(t)
                block.addWidget(d)
                page_lay.addLayout(block)
            page_lay.addStretch()
            self._pages.append(page)
            self._stack.addWidget(page)
        self._stack.setCurrentIndex(0)
        layout.addWidget(self._stack, stretch=1)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(8)
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


class ThemeCardWidget(QFrame):
    def __init__(self, theme_id, theme_name, colors, parent=None):
        super().__init__(parent)
        self.theme_id = theme_id
        self.setFixedSize(90, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        preview = QFrame()
        bg = colors.get('glass_start', colors.get('input_bg', '#1e1e1e'))
        preview.setStyleSheet(f"background: {bg}; border: none; border-radius: 6px;")
        preview.setFixedHeight(30)
        layout.addWidget(preview)

        name = QLabel(theme_name)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("color: #cccccc; font-size: 11px;")
        layout.addWidget(name)

        self._selected = False
        self._update_style()

    def _update_style(self):
        if self._selected:
            self.setStyleSheet("border: 2px solid #4fc3f7; border-radius: 8px;")
        else:
            self.setStyleSheet("border: 2px solid transparent; border-radius: 8px;")

    def set_selected(self, selected):
        self._selected = selected
        self._update_style()


class ToggleSwitchWidget(QCheckBox):
    def __init__(self, on_color="#4fc3f7", off_color="#666666", parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._on_color = on_color
        self._off_color = off_color

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.isChecked():
            painter.setBrush(QBrush(QColor(self._on_color)))
        else:
            painter.setBrush(QBrush(QColor(self._off_color)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 40, 24, 12, 12)
        painter.setBrush(QBrush(QColor("white")))
        if self.isChecked():
            painter.drawEllipse(20, 3, 18, 18)
        else:
            painter.drawEllipse(3, 3, 18, 18)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self.isChecked())
            event.accept()

    def update_colors(self, on_color, off_color):
        self._on_color = on_color
        self._off_color = off_color
        self.update()


class ToggleSwitchRow(QWidget):
    def __init__(self, text, checked=False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._label = QLabel(text)
        self._label.setWordWrap(True)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        set_label_point_size(self._label, 12)
        layout.addWidget(self._label, 1)
        theme = get_theme(self._get_theme_id())
        c = theme["colors"]
        self._toggle = ToggleSwitchWidget(
            on_color=c.get("toggle_on", "#4fc3f7"),
            off_color=c.get("toggle_off", "#666666")
        )
        self._toggle.setChecked(checked)
        self._toggle.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self._toggle, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.toggled = self._toggle.toggled
        self.stateChanged = self._toggle.stateChanged

    def _get_theme_id(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "app_state"):
                return normalize_theme_id(parent.app_state.get("theme", "dark"))
            parent = parent.parent()
        return "dark"

    def isChecked(self):
        return self._toggle.isChecked()

    def setChecked(self, checked):
        self._toggle.setChecked(checked)

    def blockSignals(self, block):
        self._toggle.blockSignals(block)


class SettingsDialog(GlassPanelDialog):
    def __init__(self, state_manager, parent=None):
        super().__init__(parent, overlap_radius=20, escape_action="close")
        self.state_manager = state_manager
        self.text_size = int(self.state_manager.state.get("taskTextSize", 14))
        self._saved_snapshot = {}
        self.history_shortcut_edit = None
        self.settings_shortcut_edit = None
        self.pin_shortcut_edit = None
        self.always_on_top_shortcut_edit = None
        self.export_shortcut_edit = None
        self._chrome = None
        self.init_ui()

    def _build_snapshot(self):
        return {
            "startOnBoot": self.startup_cb.isChecked(),
            "positionLocked": self.lock_cb.isChecked(),
            "pinnedToDesktop": self.pin_cb.isChecked(),
            "alwaysOnTop": self.always_on_top_cb.isChecked(),
            "theme": self._get_selected_theme(),
            "opacity": self.opacity_slider.value() / 100.0,
            "taskTextSize": self.text_size_slider.value(),
            "historyShortcut": self.history_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "settingsShortcut": self.settings_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "pinShortcut": self.pin_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "alwaysOnTopShortcut": self.always_on_top_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "exportShortcut": self.export_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "groupsEnabled": self.groups_enabled_cb.isChecked(),
            "checkForUpdates": self.check_updates_cb.isChecked(),
        }

    def _load_sequence(self, value, fallback):
        sequence_text = value or fallback
        return QKeySequence.fromString(sequence_text, QKeySequence.SequenceFormat.PortableText)

    def _mark_dirty(self):
        self._has_unsaved_changes = self._build_snapshot() != self._saved_snapshot

    def _select_theme(self, theme_id):
        for tid, card in self._theme_cards.items():
            card.set_selected(tid == theme_id)
        self._apply_entry_widget_theming()
        parent = self.parent()
        if parent and hasattr(parent, "app_state"):
            parent.app_state["theme"] = theme_id
            parent.apply_app_theme()
        self._mark_dirty()

    def _get_selected_theme(self):
        for tid, card in self._theme_cards.items():
            if card._selected:
                return tid
        return "dark"

    def _validate_shortcuts(self):
        all_shortcuts = [
            self.history_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            self.settings_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            self.pin_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            self.always_on_top_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            self.toggle_tray_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            self.export_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
        ]
        all_shortcuts = [shortcut for shortcut in all_shortcuts if shortcut]
        duplicates = sorted({shortcut for shortcut in all_shortcuts if all_shortcuts.count(shortcut) > 1})

        if duplicates:
            ThemedMessageDialog.warning(
                self,
                "Shortcut Conflict",
                "Shortcut keys must be unique. Conflicts found: " + ", ".join(duplicates),
            )
            return False

        return True

    def _reset_active_tab_to_defaults(self) -> None:
        tab = self._stack.currentIndex()
        if tab == 0:
            self._reset_general_tab_defaults()
        elif tab == 1:
            self._reset_appearance_tab_defaults()
        elif tab == 2:
            self._reset_shortcuts_tab_defaults()
        elif tab == 3:
            self._reset_export_tab_defaults()
        elif tab == 4:
            self._reset_reminders_tab_defaults()
        elif tab == 5:
            self._reset_advanced_tab_defaults()
        elif tab == 6:
            self._reset_help_tab_defaults()
        self._mark_dirty()

    def _reset_general_tab_defaults(self):
        self.startup_cb.setChecked(False)
        self.lock_cb.setChecked(False)
        self.pin_cb.setChecked(False)
        self.always_on_top_cb.setChecked(False)
        self.check_updates_cb.setChecked(True)
        self.boot_notification_cb.setChecked(True)

    def _reset_appearance_tab_defaults(self):
        self._select_theme("dark")
        self.text_size_slider.setValue(14)
        self.opacity_slider.setValue(100)

    def _reset_shortcuts_tab_defaults(self) -> None:
        defaults = {
            "history_shortcut_edit": "Ctrl+H",
            "settings_shortcut_edit": "Ctrl+,",
            "pin_shortcut_edit": "Ctrl+P",
            "always_on_top_shortcut_edit": "Alt+T",
            "toggle_tray_shortcut_edit": "Ctrl+M",
            "export_shortcut_edit": "Ctrl+E",
        }
        for attr, seq_str in defaults.items():
            edit = getattr(self, attr, None)
            if edit is None:
                continue
            edit.setKeySequence(QKeySequence.fromString(seq_str, QKeySequence.SequenceFormat.PortableText))

    def _reset_export_tab_defaults(self):
        idx = self.export_format_combo.findData("txt")
        if idx >= 0:
            self.export_format_combo.setCurrentIndex(idx)
        self.export_include_history_cb.setChecked(False)

    def _reset_reminders_tab_defaults(self):
        pass

    def _reset_advanced_tab_defaults(self):
        self.groups_enabled_cb.setChecked(True)

    def _reset_help_tab_defaults(self):
        pass

    def _create_tab_label(self, text):
        label = QLabel(text)
        set_label_point_size(label, 14)
        return label

    def _create_checkbox_row(self, text, checked):
        row = ToggleSwitchRow(text, checked)
        row.stateChanged.connect(lambda _: self._mark_dirty())
        return row

    def _create_toggle_row(self, text, checked):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(text)
        set_label_point_size(label, 14)
        layout.addWidget(label)
        layout.addStretch()
        toggle = ToggleSwitchWidget()
        toggle.setChecked(checked)
        toggle.stateChanged.connect(lambda _: self._mark_dirty())
        layout.addWidget(toggle)
        row._toggle = toggle
        return row

    def init_ui(self):
        self.setWindowTitle("Settings")
        self.setWindowIcon(get_app_icon())
        from PyQt6.QtWidgets import QApplication
        screen = self.screen() or (QApplication.primaryScreen() if QApplication.instance() else None)
        saved_w, saved_h = self.state_manager.get_settings_window_size()
        if screen:
            available = screen.availableGeometry()
            max_h = available.height() - 80
            max_w = available.width() - 80
            w = min(saved_w, max_w)
            h = min(saved_h, max_h)
        else:
            w, h = saved_w, saved_h
        self.resize(w, h)
        self.setMinimumSize(400, 460)
        self.setMouseTracking(True)
        self._chrome = FramelessChromeController(self, min_width=400, min_height=460)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(8)

        title = QLabel("Settings")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        # Visual separator between title and content
        title_sep = QFrame()
        title_sep.setObjectName("hSeparator")
        title_sep.setFrameShape(QFrame.Shape.HLine)
        title_sep.setFixedHeight(1)
        layout.addWidget(title_sep)

        # ── General Tab (content) ──
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setContentsMargins(6, 8, 6, 6)
        general_layout.setSpacing(12)

        self.startup_cb = self._create_checkbox_row("Run on Startup (Registry)", self.state_manager.state.get("startOnBoot", False))
        general_layout.addWidget(self.startup_cb)

        self.lock_cb = self._create_checkbox_row("Lock Window Position", self.state_manager.state.get("positionLocked", False))
        general_layout.addWidget(self.lock_cb)

        self.pin_cb = self._create_checkbox_row("Pin to Desktop Background", self.state_manager.state.get("pinnedToDesktop", False))
        general_layout.addWidget(self.pin_cb)

        self.always_on_top_cb = self._create_checkbox_row("Always on Top", self.state_manager.state.get("alwaysOnTop", False))
        general_layout.addWidget(self.always_on_top_cb)

        self.pin_cb.toggled.connect(self._on_pin_to_desktop_toggled)
        self.always_on_top_cb.toggled.connect(self._on_always_on_top_toggled)

        # mutual_excl_note = QLabel("These options are mutually exclusive.")
        # mutual_excl_note.setStyleSheet("opacity: 0.6; font-size: 11px; font-style: italic;")
        # mutual_excl_note.setContentsMargins(0, 0, 0, 4)
        # general_layout.addWidget(mutual_excl_note)

        self.check_updates_cb = self._create_checkbox_row("Check for updates at startup", self.state_manager.state.get("checkForUpdates", True))
        general_layout.addWidget(self.check_updates_cb)

        self.boot_notification_cb = self._create_checkbox_row("Show boot notification for pending tasks", self.state_manager.state.get("showBootNotification", True))
        general_layout.addWidget(self.boot_notification_cb)

        # Reminders shortcut
        reminders_shortcut_row = QHBoxLayout()
        reminders_shortcut_row.setSpacing(8)
        reminders_shortcut_label = QLabel("Reminders shortcut")
        reminders_shortcut_label.setStyleSheet("font-weight: 600;")
        reminders_shortcut_row.addWidget(reminders_shortcut_label)
        reminders_shortcut_row.addStretch()
        self.reminders_shortcut_edit = QKeySequenceEdit()
        self.reminders_shortcut_edit.setFixedWidth(120)
        self.reminders_shortcut_edit.setToolTip("Click and press the desired key combination to open Reminders")
        self.reminders_shortcut_edit.setKeySequence(self._load_sequence(self.state_manager.state.get("remindersShortcut"), ""))
        self.reminders_shortcut_edit.keySequenceChanged.connect(self._mark_dirty)
        _glow = QGraphicsDropShadowEffect(self.reminders_shortcut_edit)
        _glow.setBlurRadius(30)
        _glow.setOffset(0, 0)
        _glow.setColor(QColor(0, 0, 0, 0))
        self.reminders_shortcut_edit.setGraphicsEffect(_glow)
        self.reminders_shortcut_edit._glow = _glow
        self.reminders_shortcut_edit.installEventFilter(self)
        reminders_shortcut_row.addWidget(self.reminders_shortcut_edit)
        general_layout.addLayout(reminders_shortcut_row)

        general_layout.addStretch()

        # ── Appearance Tab (content) ──
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        appearance_layout.setContentsMargins(6, 8, 6, 6)
        appearance_layout.setSpacing(14)

        # Theme
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("font-weight: 600;")
        appearance_layout.addWidget(theme_label)

        theme_cards_layout = QHBoxLayout()
        theme_cards_layout.setSpacing(6)
        self._theme_cards = {}
        saved_theme = normalize_theme_id(self.state_manager.state.get("theme", "dark"))
        for tid in ["dark", "light", "oled"]:
            colors = get_theme(tid)["colors"]
            card = ThemeCardWidget(tid, tid.capitalize(), colors)
            card.mousePressEvent = lambda _, t=tid: self._select_theme(t)
            theme_cards_layout.addWidget(card)
            self._theme_cards[tid] = card
        self._theme_cards[saved_theme].set_selected(True)
        self._initial_theme = saved_theme
        theme_cards_layout.addStretch()
        appearance_layout.addLayout(theme_cards_layout)

        # Task text size — label shows live value
        text_size_row = QHBoxLayout()
        text_size_row.setSpacing(8)
        text_size_label_title = QLabel("Task text size")
        text_size_label_title.setStyleSheet("font-weight: 600;")
        text_size_row.addWidget(text_size_label_title)
        text_size_row.addStretch()
        self.text_size_label = QLabel()
        self.text_size_label.setStyleSheet("opacity: 0.7;")
        self.text_size_label.setMinimumWidth(48)
        self.text_size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        text_size_row.addWidget(self.text_size_label)
        appearance_layout.addLayout(text_size_row)

        self.text_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.text_size_slider.setMinimum(16)
        self.text_size_slider.setMaximum(25)
        self.text_size_slider.setValue(int(self.state_manager.state.get("taskTextSize", 14)))
        self.text_size_slider.valueChanged.connect(self.update_text_size_label)
        self.text_size_slider.valueChanged.connect(self._mark_dirty)
        self.text_size_slider.valueChanged.connect(self._emit_text_size_to_parent)
        appearance_layout.addWidget(self.text_size_slider)
        self.update_text_size_label(self.text_size_slider.value())

        # Opacity — label shows live value
        opacity_row = QHBoxLayout()
        opacity_row.setSpacing(8)
        opacity_label = QLabel("Window opacity")
        opacity_label.setStyleSheet("font-weight: 600;")
        opacity_row.addWidget(opacity_label)
        opacity_row.addStretch()
        self.opacity_value_label = QLabel()
        self.opacity_value_label.setStyleSheet("opacity: 0.7;")
        self.opacity_value_label.setMinimumWidth(48)
        self.opacity_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        opacity_row.addWidget(self.opacity_value_label)
        appearance_layout.addLayout(opacity_row)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(30)
        self.opacity_slider.setMaximum(100)
        current_opacity = max(30, int(self.state_manager.state.get("opacity", 1.0) * 100))
        self.opacity_slider.setValue(current_opacity)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        self.opacity_slider.valueChanged.connect(self._mark_dirty)
        appearance_layout.addWidget(self.opacity_slider)
        self._on_opacity_changed(self.opacity_slider.value())

        # Mouse glow toggle
        mouse_glow_row = QHBoxLayout()
        mouse_glow_label = QLabel("Mouse glow effect")
        mouse_glow_label.setStyleSheet("font-weight: 600;")
        mouse_glow_row.addWidget(mouse_glow_label)
        mouse_glow_row.addStretch()
        self.mouse_glow_toggle = ToggleSwitchWidget()
        self.mouse_glow_toggle.setChecked(self.state_manager.state.get("mouseGlow", True))
        self.mouse_glow_toggle.toggled.connect(self._mark_dirty)
        self.mouse_glow_toggle.toggled.connect(self._on_mouse_glow_toggled)
        mouse_glow_row.addWidget(self.mouse_glow_toggle)
        appearance_layout.addLayout(mouse_glow_row)

        appearance_layout.addStretch()

        # ── Keyboard Shortcuts Tab (content) ──
        shortcuts_tab = QWidget()
        shortcuts_outer_layout = QVBoxLayout(shortcuts_tab)
        shortcuts_outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        shortcuts_layout = QVBoxLayout(scroll_content)
        shortcuts_layout.setContentsMargins(6, 8, 6, 6)
        shortcuts_layout.setSpacing(6)

        def _add_section_label(text: str) -> None:
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: bold; padding-top: 4px;")
            shortcuts_layout.addWidget(lbl)

        def _add_shortcut_row(title: str, hint: str | None, default_seq: str, attr_name: str, state_key: str) -> None:
            card = QFrame()
            card.setObjectName("nestedPanel")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 6, 10, 6)
            card_layout.setSpacing(8)

            text_col = QVBoxLayout()
            text_col.setContentsMargins(0, 0, 0, 0)
            text_col.setSpacing(0)
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("font-weight: 600;")
            text_col.addWidget(title_lbl)
            if hint:
                hint_lbl = QLabel(hint)
                hint_lbl.setStyleSheet("opacity: 0.7;")
                hint_lbl.setWordWrap(True)
                text_col.addWidget(hint_lbl)
            card_layout.addLayout(text_col, 1)

            edit = QKeySequenceEdit()
            edit.setFixedWidth(120)
            edit.setToolTip("Click and press the desired key combination to record it")
            edit.setKeySequence(self._load_sequence(self.state_manager.state.get(state_key), default_seq))
            edit.keySequenceChanged.connect(self._mark_dirty)

            glow = QGraphicsDropShadowEffect(edit)
            glow.setBlurRadius(30)
            glow.setOffset(0, 0)
            glow.setColor(QColor(0, 0, 0, 0))
            edit.setGraphicsEffect(glow)
            edit._glow = glow
            edit.installEventFilter(self)

            if attr_name == "toggle_tray_shortcut_edit":
                def _on_tray_edit_focus(in_focus, _edit=edit):
                    parent = self.parent()
                    if parent is None:
                        return
                    if in_focus:
                        if parent._tray_hotkey_id is not None:
                            parent._hotkey_filter.unregister(parent._tray_hotkey_id)
                            parent._tray_hotkey_id = None
                    else:
                        new_seq = _edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
                        if new_seq:
                            hid = parent._hotkey_filter.register(new_seq, parent._toggle_tray_visibility)
                            if hid is not None:
                                parent._tray_hotkey_id = hid
                edit.installEventFilter(self)
                edit._tray_focus_handler = _on_tray_edit_focus
            card_layout.addWidget(edit, 0, Qt.AlignmentFlag.AlignRight)
            setattr(self, attr_name, edit)
            shortcuts_layout.addWidget(card)

        _add_section_label("Window")
        _add_shortcut_row("Open History", "Show the completed-tasks log.", "Ctrl+H",
                          "history_shortcut_edit", "historyShortcut")
        _add_shortcut_row("Open Settings", "Open the settings dialog.", "Ctrl+,",
                          "settings_shortcut_edit", "settingsShortcut")
        _add_shortcut_row("Pin to Screen", "Toggle wallpaper-pin mode.", "Ctrl+P",
                          "pin_shortcut_edit", "pinShortcut")
        _add_shortcut_row("Always on Top", "Toggle always-on-top window mode.", "Alt+T",
                          "always_on_top_shortcut_edit", "alwaysOnTopShortcut")
        _add_shortcut_row("Minimize/Restore to Tray", "Hide to or restore from system tray.", "Ctrl+M",
                          "toggle_tray_shortcut_edit", "toggleTrayShortcut")

        _add_section_label("Actions")
        _add_shortcut_row("Export", "Open the export dialog.", "Ctrl+E",
                          "export_shortcut_edit", "exportShortcut")

        shortcuts_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        shortcuts_outer_layout.addWidget(scroll_area)

        # ── Export Tab (content) ──
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        export_layout.setContentsMargins(6, 8, 6, 6)
        export_layout.setSpacing(8)

        # ── Format section ──
        format_label = QLabel("Format")
        format_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        export_layout.addWidget(format_label)
        self.export_format_combo = QComboBox()
        self.export_format_combo.setMinimumHeight(26)
        self.export_format_combo.addItem("Plain Text (.txt)", "txt")
        self.export_format_combo.addItem("Markdown (.md)", "md")
        self.export_format_combo.addItem("CSV (.csv)", "csv")
        export_layout.addWidget(self.export_format_combo)

        # ── Options section ──
        options_label = QLabel("Options")
        options_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        export_layout.addWidget(options_label)
        self.export_include_history_cb = QCheckBox("Include history")
        self.export_include_history_cb.setChecked(False)
        self.export_include_history_cb.setStyleSheet("font-size: 14px;")
        self.export_include_history_cb.stateChanged.connect(self._mark_dirty)
        export_layout.addWidget(self.export_include_history_cb)

        # ── Group filter section (always created; visibility toggled by state) ──
        self._export_group_filter = {}  # groupId -> QCheckBox
        self._export_all_groups_cb: QCheckBox | None = None
        self._export_filter_label = QLabel("Groups to export")
        self._export_filter_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        export_layout.addWidget(self._export_filter_label)

        self._export_filter_card = QFrame()
        self._export_filter_card.setObjectName("nestedPanel")
        card_layout = QVBoxLayout(self._export_filter_card)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(2)

        self._export_all_groups_cb = QCheckBox("All groups")
        self._export_all_groups_cb.setChecked(True)
        self._export_all_groups_cb.setStyleSheet("font-size: 14px; font-weight: bold;")
        self._export_all_groups_cb.toggled.connect(self._on_export_all_groups_toggled)
        card_layout.addWidget(self._export_all_groups_cb)

        sep = QFrame()
        sep.setObjectName("hSeparator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        card_layout.addWidget(sep)

        self._export_group_scroll = QScrollArea()
        self._export_group_scroll.setWidgetResizable(True)
        self._export_group_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._export_group_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._export_group_scroll.setStyleSheet("border: none; background: transparent;")
        self._export_group_scroll.setMinimumHeight(36)
        self._export_group_scroll.setMaximumHeight(120)

        self._export_group_content = QWidget()
        self._export_group_content.setObjectName("transparentSurface")
        self._export_group_cl = QVBoxLayout(self._export_group_content)
        self._export_group_cl.setContentsMargins(14, 4, 4, 4)
        self._export_group_cl.setSpacing(3)

        self._export_group_scroll.setWidget(self._export_group_content)
        card_layout.addWidget(self._export_group_scroll)

        export_layout.addWidget(self._export_filter_card)

        self._populate_export_group_filter()
        self._update_export_groups_filter()

        export_layout.addStretch()

        self.export_btn = QPushButton("Export Tasks…")
        self.export_btn.setObjectName("primaryButton")
        self.export_btn.setMinimumHeight(32)
        self.export_btn.clicked.connect(self._run_settings_export)
        export_layout.addWidget(self.export_btn)

        # ── Advanced Tab (content) ──
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        advanced_layout.setContentsMargins(6, 8, 6, 6)
        advanced_layout.setSpacing(12)

        self.groups_enabled_cb = self._create_checkbox_row(
            "Enable task groups",
            self.state_manager.state.get("groupsEnabled", True),
        )
        advanced_layout.addWidget(self.groups_enabled_cb)

        advanced_layout.addStretch()

        # ── Reminders Tab (content) ──
        reminders_tab = QWidget()
        reminders_layout = QVBoxLayout(reminders_tab)
        reminders_layout.setContentsMargins(6, 8, 6, 6)
        reminders_layout.setSpacing(12)

        reminders_title = self._create_tab_label("Reminders")
        reminders_layout.addWidget(reminders_title)

        reminders_sep = QFrame()
        reminders_sep.setObjectName("hSeparator")
        reminders_sep.setFrameShape(QFrame.Shape.HLine)
        reminders_sep.setFixedHeight(1)
        reminders_layout.addWidget(reminders_sep)

        task_reminder_label = QLabel("Pending Task Reminders")
        set_label_point_size(task_reminder_label, 12)
        task_reminder_label.setStyleSheet("font-weight: 600;")
        reminders_layout.addWidget(task_reminder_label)

        self._task_reminder_list = QListWidget()
        self._task_reminder_list.itemDoubleClicked.connect(self._edit_task_reminder_from_list)
        reminders_layout.addWidget(self._task_reminder_list, 1)

        clear_reminder_btn = QPushButton("Clear Selected")
        clear_reminder_btn.setObjectName("ghostButton")
        clear_reminder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_reminder_btn.clicked.connect(self._clear_selected_task_reminder)
        reminders_layout.addWidget(clear_reminder_btn)

        reminders_layout.addStretch()

        # ── Help Tab (content) ──
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)
        help_layout.setContentsMargins(6, 8, 6, 6)
        help_layout.setSpacing(12)

        tutorial_btn = QPushButton("Show welcome guide")
        tutorial_btn.setObjectName("primaryButton")
        tutorial_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tutorial_btn.clicked.connect(self._open_tutorial)
        help_layout.addWidget(tutorial_btn)

        reminders_btn = QPushButton("\u23f1\ufe0f Reminders")
        reminders_btn.setObjectName("primaryButton")
        reminders_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reminders_btn.clicked.connect(self._open_reminders_from_settings)
        help_layout.addWidget(reminders_btn)

        support_btn = QPushButton("\u2764\ufe0f Support Development")
        support_btn.setObjectName("primaryButton")
        support_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        support_btn.clicked.connect(self._open_support_from_settings)
        help_layout.addWidget(support_btn)

        help_layout.addStretch()

        # ── Sidebar layout: buttons on the left, stacked content on the right ──
        content_row = QHBoxLayout()
        content_row.setSpacing(8)

        self._sidebar_layout = QVBoxLayout()
        self._sidebar_layout.setSpacing(4)
        self._sidebar_layout.setContentsMargins(0, 0, 0, 0)
        tab_names = ["General", "Appearance", "Shortcuts", "Export", "Reminders", "Advanced", "Help"]
        tab_icons = {
            "General": "\u2699",
            "Appearance": "\U0001f3a8",
            "Shortcuts": "\u2328",
            "Export": "\U0001f4e4",
            "Reminders": "\U0001f514",
            "Advanced": "\U0001f527",
            "Help": "\u2753",
        }
        self._page_buttons = []
        self._stack = QStackedWidget()
        self._stack.addWidget(general_tab)
        self._stack.addWidget(appearance_tab)
        self._stack.addWidget(shortcuts_tab)
        self._stack.addWidget(export_tab)
        self._stack.addWidget(reminders_tab)
        self._stack.addWidget(advanced_tab)
        self._stack.addWidget(help_tab)

        for i, name in enumerate(tab_names):
            icon = tab_icons.get(name, "")
            btn = QPushButton(f"  {icon}  {name}")
            btn.setObjectName("sidebarButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(32)
            btn.setToolTip(f"Open {name} settings")
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))
            self._sidebar_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignLeft)
            self._page_buttons.append(btn)

        self._sidebar_layout.addStretch()

        right_column = QVBoxLayout()
        right_column.setSpacing(8)
        right_column.addWidget(self._stack, 1)

        # Reset to Defaults button - always visible above Save/Close
        self.reset_shortcuts_btn = QPushButton("Reset to Defaults")
        self.reset_shortcuts_btn.setObjectName("ghostButton")
        self.reset_shortcuts_btn.setMinimumHeight(28)
        self.reset_shortcuts_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_shortcuts_btn.clicked.connect(self._reset_active_tab_to_defaults)
        right_column.addWidget(self.reset_shortcuts_btn)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.save_changes)
        button_row.addWidget(self.save_btn, 1)

        self.close_btn = QPushButton("Close")
        self.close_btn.setObjectName("primaryButton")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setDefault(True)
        self.close_btn.clicked.connect(self.close)
        button_row.addWidget(self.close_btn, 1)

        right_column.addLayout(button_row)

        content_row.addLayout(self._sidebar_layout, 0)
        content_row.addLayout(right_column, 1)
        layout.addLayout(content_row)

        self._switch_page(0)

        self._saved_snapshot = self._build_snapshot()
        self._has_unsaved_changes = False
        self._update_overlap_opacity()
        self._populate_task_reminder_list()
        self._apply_entry_widget_theming()

    def _apply_entry_widget_theming(self):
        from PyQt6.QtWidgets import QScrollArea
        theme = get_theme(self._get_theme_id())
        c = theme["colors"]
        r = theme["radii"]
        input_r = r.get("input", r.get("small", 4))
        glass_bg = c.get("glass_start", "rgba(30,30,30,220)")
        for frame in self.findChildren(QFrame):
            if frame.objectName() == "nestedPanel":
                frame.setStyleSheet(f"""
                    background: {c.get("input_bg", "rgba(0,0,0,40)")};
                    border: none;
                    border-radius: {input_r}px;
                """)
        for sa in self.findChildren(QScrollArea):
            sa.setStyleSheet(f"""
                QScrollArea {{
                    background: transparent;
                    border: none;
                }}
                QScrollBar:vertical {{
                    background: transparent;
                    width: 8px;
                }}
                QScrollBar::handle:vertical {{
                    background: {c.get("scrollbar", "rgba(255,255,255,80)")};
                    border-radius: 4px;
                    min-height: 20px;
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
            """)
            widget = sa.widget()
            if widget:
                widget.setStyleSheet("background: transparent;")
        input_css = f"""
            background: {c.get("input_bg", "rgba(0,0,0,40)")};
            border: 1px solid {c.get("border", "rgba(255,255,255,60)")};
            border-radius: {input_r}px;
            color: {c.get("text", "#ffffff")};
            padding: 4px 8px;
        """
        for w in self.findChildren(QKeySequenceEdit):
            w.setStyleSheet(input_css)
        for w in self.findChildren(QComboBox):
            w.setStyleSheet(input_css)

    def _on_pin_to_desktop_toggled(self, checked: bool):
        if checked:
            self.always_on_top_cb.blockSignals(True)
            self.always_on_top_cb.setChecked(False)
            self.always_on_top_cb.blockSignals(False)
        self._mark_dirty()

    def _on_always_on_top_toggled(self, checked: bool):
        if checked:
            self.pin_cb.blockSignals(True)
            self.pin_cb.setChecked(False)
            self.pin_cb.blockSignals(False)
        self._mark_dirty()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.oldSize().isValid():
            self.state_manager.save_settings_window_size(event.size().width(), event.size().height())

    def _get_theme_id(self):
        return normalize_theme_id(self.state_manager.state.get("theme", "dark"))

    def _switch_page(self, index: int):
        for i, btn in enumerate(self._page_buttons):
            btn.setChecked(i == index)
        self._stack.setCurrentIndex(index)

    def _open_tutorial(self):
        parent = self.parent()
        if parent is not None and hasattr(parent, "_show_tutorial"):
            parent._show_tutorial()

    def _open_whats_new(self):
        parent = self.parent()
        if parent is not None and hasattr(parent, "_show_whats_new"):
            parent._show_whats_new()

    def _open_reminders_from_settings(self):
        self._switch_page(4)

    def _open_support_from_settings(self):
        parent = self.parent()
        if parent is not None and hasattr(parent, "_open_support_dialog"):
            parent._open_support_dialog()

    def _populate_task_reminder_list(self):
        self._task_reminder_list.clear()
        parent = self.parent()
        if parent is None or not hasattr(parent, '_timer_manager'):
            return
        now_ts = datetime.now().timestamp()
        for cfg_dict in parent._timer_manager.to_list():
            if cfg_dict.get("taskId") is None:
                continue
            if not cfg_dict.get("enabled", True):
                continue
            trigger_at = cfg_dict.get("nextTriggerAt", 0)
            if trigger_at <= now_ts:
                continue
            remaining = int(trigger_at - now_ts)
            hours, remainder = divmod(remaining, 3600)
            minutes, secs = divmod(remainder, 60)
            if hours > 0:
                time_str = f"{hours}h {minutes}m"
            elif minutes > 0:
                time_str = f"{minutes}m {secs}s"
            else:
                time_str = f"{secs}s"
            name = cfg_dict.get("name", "Task reminder")
            label = f"{name[:60]}  \u2014 {time_str}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, cfg_dict.get("taskId"))
            self._task_reminder_list.addItem(item)

    def _clear_task_reminder_from_list(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole)
        parent = self.parent()
        if parent is not None and hasattr(parent, '_timer_manager'):
            parent._timer_manager.cancel_task_reminder(task_id)
            parent.app_state["timers"] = parent._timer_manager.to_list()
            parent.state_manager.save()
            self._populate_task_reminder_list()

    def _edit_task_reminder_from_list(self, item):
        task_id = item.data(Qt.ItemDataRole.UserRole)
        parent = self.parent()
        if parent is None:
            return
        task = next((t for t in parent.tasks if t["id"] == task_id), None)
        if task is not None:
            parent._show_custom_reminder_dialog(task)
            self._populate_task_reminder_list()

    def _clear_selected_task_reminder(self):
        item = self._task_reminder_list.currentItem()
        if item is None:
            return
        if not ThemedMessageDialog.question(self, "Clear Reminder", "Are you sure you want to clear the selected reminder?"):
            return
        self._clear_task_reminder_from_list(item)

    def _on_export_all_groups_toggled(self, checked):
        self._export_group_bulk_update = True
        try:
            for cb in self._export_group_filter.values():
                cb.setChecked(checked)
        finally:
            self._export_group_bulk_update = False

    def _on_export_group_changed(self):
        if getattr(self, "_export_group_bulk_update", False):
            return
        all_checked = all(cb.isChecked() for cb in self._export_group_filter.values())
        self._export_all_groups_cb.blockSignals(True)
        self._export_all_groups_cb.setChecked(all_checked)
        self._export_all_groups_cb.blockSignals(False)

    def _populate_export_group_filter(self) -> None:
        parent = self.parent()
        groups_data = parent.groups_data if parent else {"groups": []}
        all_groups = sorted_groups(groups_data)
        while self._export_group_cl.count():
            item = self._export_group_cl.takeAt(0)
            w = item.widget() if item is not None else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._export_group_filter = {}
        for g in all_groups:
            cb = QCheckBox(g["name"])
            cb.setChecked(True)
            cb.setStyleSheet("font-size: 14px;")
            cb.stateChanged.connect(self._on_export_group_changed)
            self._export_group_filter[g["id"]] = cb
            self._export_group_cl.addWidget(cb)
        self._export_group_cl.addStretch()

    def _update_export_groups_filter(self) -> None:
        parent = self.parent()
        groups_enabled = parent.app_state.get("groupsEnabled", True) if parent else True
        groups_data = parent.groups_data if parent else {"groups": []}
        all_groups = sorted_groups(groups_data)
        has_filter = groups_enabled and len(all_groups) > 1
        self._export_filter_label.setVisible(has_filter)
        self._export_filter_card.setVisible(has_filter)

    def _run_settings_export(self):
        from src.backend.export_service import run_export_with_dialog

        export_format = self.export_format_combo.currentData()
        parent = self.parent()
        if parent is None:
            return

        run_export_with_dialog(
            parent_widget=self,
            main_window=parent,
            export_format=export_format,
            include_history=self.export_include_history_cb.isChecked(),
            group_filter=self._export_group_filter,
            all_groups_checked=self._export_all_groups_cb.isChecked(),
        )

    def eventFilter(self, obj, event):
        if hasattr(obj, '_tray_focus_handler'):
            if event.type() == QEvent.Type.FocusIn:
                obj._tray_focus_handler(True)
            elif event.type() == QEvent.Type.FocusOut:
                obj._tray_focus_handler(False)
        if isinstance(obj, QKeySequenceEdit) and hasattr(obj, '_glow'):
            theme_id = normalize_theme_id(self.state_manager.state.get("theme", "dark"))
            accent = get_theme(theme_id)["colors"].get("toggle_on", "#4fc3f7")
            if event.type() == QEvent.Type.FocusIn:
                c = QColor(accent)
                c.setAlpha(150)
                obj._glow.setColor(c)
            elif event.type() == QEvent.Type.FocusOut:
                obj._glow.setColor(QColor(0, 0, 0, 0))
        return super().eventFilter(obj, event)

    def save_changes(self):
        if not self._validate_shortcuts():
            return False

        self.state_manager.set_run_on_startup(self.startup_cb.isChecked())
        self.state_manager.state["positionLocked"] = self.lock_cb.isChecked()
        self.state_manager.state["pinnedToDesktop"] = self.pin_cb.isChecked()
        self.state_manager.state["alwaysOnTop"] = self.always_on_top_cb.isChecked()
        parent = self.parent()
        reconcile_layer_settings(self.state_manager.state)
        if parent is not None and hasattr(parent, "_apply_window_layer"):
            parent._apply_window_layer()

        self.state_manager.state["theme"] = normalize_theme_id(self._get_selected_theme())
        opacity = self.opacity_slider.value() / 100.0
        self.state_manager.state["opacity"] = opacity
        self.state_manager.state["taskTextSize"] = self.text_size_slider.value()
        self.state_manager.state["mouseGlow"] = self.mouse_glow_toggle.isChecked()
        self.state_manager.state["historyShortcut"] = self.history_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Ctrl+H"
        self.state_manager.state["settingsShortcut"] = self.settings_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Ctrl+,"
        self.state_manager.state["pinShortcut"] = self.pin_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Ctrl+P"
        self.state_manager.state["toggleTrayShortcut"] = self.toggle_tray_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Ctrl+M"
        self.state_manager.state["alwaysOnTopShortcut"] = self.always_on_top_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Alt+T"
        self.state_manager.state["exportShortcut"] = self.export_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Ctrl+E"
        self.state_manager.state["remindersShortcut"] = self.reminders_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or ""
        parent = self.parent()
        old_groups_enabled = parent.app_state.get("groupsEnabled", True) if (parent is not None and hasattr(parent, "task_row_widgets")) else True
        self.state_manager.state["groupsEnabled"] = self.groups_enabled_cb.isChecked()
        self.state_manager.state["checkForUpdates"] = self.check_updates_cb.isChecked()
        self.state_manager.state["showBootNotification"] = self.boot_notification_cb.isChecked()
        self.state_manager.save()
        self._saved_snapshot = self._build_snapshot()
        self._has_unsaved_changes = False

        if parent is not None and hasattr(parent, "task_row_widgets"):
            groups_changed = self.groups_enabled_cb.isChecked() != old_groups_enabled
            parent.app_state["groupsEnabled"] = self.groups_enabled_cb.isChecked()
            parent.setUpdatesEnabled(False)
            theme_changed = normalize_theme_id(getattr(self, "_initial_theme", "dark")) != normalize_theme_id(self.state_manager.state.get("theme", "dark"))
            if theme_changed:
                parent.apply_app_theme()
            parent.setWindowOpacity(opacity)
            if groups_changed:
                self._populate_export_group_filter()
                self._update_export_groups_filter()
                parent.render_tasks()  # FIX-A1: groups changed — full re-render needed
            else:
                parent.task_text_size = int(self.state_manager.state.get("taskTextSize", 14))
                for row in parent.task_row_widgets.values():
                    if hasattr(row, "set_text_size"):
                        row.set_text_size(parent.task_text_size)
                parent._sync_task_row_text_layouts()
            parent.setUpdatesEnabled(True)
            parent.update()
            self._initial_theme = normalize_theme_id(self.state_manager.state.get("theme", "dark"))

        refresh_glass_shells(
            self,
            normalize_theme_id(self.state_manager.state.get("theme", "dark")),
        )
        if parent is not None:
            refresh_glass_shells(
                parent,
                normalize_theme_id(self.state_manager.state.get("theme", "dark")),
            )

        self._apply_entry_widget_theming()

        return True

    def update_text_size_label(self, value):
        self.text_size_label.setText(f"{value}px")

    def _on_opacity_changed(self, value):
        self.opacity_value_label.setText(f"{value}%")
        parent = self.parent()
        if parent is not None:
            parent.setWindowOpacity(value / 100.0)

    def _emit_text_size_to_parent(self, value):
        parent = self.parent()
        if parent is not None and hasattr(parent, "task_text_size"):
            parent.task_text_size = value
            parent.state_manager.state["taskTextSize"] = value
            if hasattr(parent, "render_tasks"):
                parent.render_tasks()

    def _on_mouse_glow_toggled(self, checked):
        parent = self.parent()
        if parent is not None and hasattr(parent, '_glow_overlay'):
            if not checked:
                parent._glow_overlay.hide_glow()
            parent.app_state["mouseGlow"] = checked

    def has_unsaved_changes(self):
        return self._build_snapshot() != self._saved_snapshot

    def closeEvent(self, event):
        if self.has_unsaved_changes():
            if ThemedMessageDialog.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes, do you want to save them?",
                default_yes=False,
            ):
                if not self.save_changes():
                    event.ignore()
                    return
            else:
                event.accept()
                self.reject()
                return

        event.accept()
        self.reject()

class MainWindow(QMainWindow):
    _update_check_done = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        
        # Frameless resize / title-bar drag (Stage 2)
        self._frameless_chrome = None

        # Initialize Backend Store and load tasks
        self.store = TaskStore("tasks.json")
        self.tasks = migrate_tasks_group_ids(self.store.load())
        self.store.save(self.tasks)

        self.group_store = GroupStore("groups.json")
        self.groups_data = self.group_store.load()
        self.group_sections = {}
        
        # Initialize History Store
        self.history_store = TaskStore("history.json")
        self.migrate_completed_tasks_to_history()
        
        # Initialize State Manager
        self.state_manager = StateManager("appstate.json")
        self.app_state = self.state_manager.load()
        if self.app_state.get("pinnedToDesktop") and self.app_state.get("alwaysOnTop"):
            reconcile_layer_settings(self.app_state)
            self.state_manager.save()
        self.task_text_size = int(self.app_state.get("taskTextSize", 14))
        self.title_label = None
        self.history_shortcut = None
        self.settings_shortcut = None
        self.pin_shortcut = None
        self.always_on_top_shortcut = None
        self.toggle_tray_shortcut = None
        self.export_shortcut = None
        self._tray_hotkey_id = None
        self.task_row_widgets = {}
        self._active_side_dialog = None
        self._history_dialog = None
        self._settings_dialog = None
        self._export_dialog = None
        self._escape_count = 0
        self._escape_timer = QTimer(self)
        self._escape_timer.setSingleShot(True)
        self._escape_timer.timeout.connect(lambda: setattr(self, '_escape_count', 0))
        self._last_archived_task = None

        self._hotkey_filter = GlobalHotkeyFilter()
        QApplication.instance().installNativeEventFilter(self._hotkey_filter)
        self._hotkey_filter.set_hwnd(int(self.winId()))

        self._escape_sc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._escape_sc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._escape_sc.activated.connect(self._on_escape_pressed)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._sync_task_row_text_layouts)

        self.init_ui()
        from PyQt6.QtWidgets import QApplication as _QA
        _QA.instance().installEventFilter(self)
        self._restore_window_geometry()
        self.init_keyboard_shortcuts()
        
        # Render any loaded tasks on boot
        self.render_tasks()  # FIX-A1: initial load — full render required
        
        # Check for lingering tasks from yesterday and notify
        if self.app_state.get("showBootNotification", True):
            BootChecker.check_and_notify(self.tasks)
        
        # Apply visual and functional settings from state
        self.apply_settings()

        # Ensure DWM shadow is disabled after the window is fully shown
        QTimer.singleShot(100, self._reapply_dwm_shadow_disable)
        QTimer.singleShot(500, self._reapply_dwm_shadow_disable)

        # Thread-safe update check result handler
        self._update_check_done.connect(self._on_update_check_done)

        # Boot-time update check (deferred 3s so UI can finish rendering first)
        if self.app_state.get("checkForUpdates", True):
            QTimer.singleShot(3000, self._check_and_prompt_update)

        # System tray (minimize-to-tray support)
        from PyQt6.QtWidgets import QApplication as _app
        self._tray = SystemTrayManager(_app.instance(), get_app_icon(), self)
        self._tray.show_requested.connect(self._show_from_tray)
        self._tray.quit_requested.connect(self._quit_from_tray)
        self._tray.settings_requested.connect(self.open_settings)
        self._tray.update_requested.connect(self._check_and_prompt_update)

        # Timer / reminder system
        from src.backend.timer_manager import TimerManager
        self._timer_manager = TimerManager(self)
        self._timer_manager.load(self.app_state.get("timers", []))
        self._migrate_task_reminders()
        self._timer_manager.timer_fired.connect(self._on_timer_fired)
        self._tray.reminders_requested.connect(self._open_reminders)
        self.app_state["timers"] = self._timer_manager.to_list()

        # First-launch tutorial
        if not self.app_state.get("seenTutorial"):
            self._show_tutorial()

        # "What's New" popup after an update — deferred so UI is ready
        last_seen = self.app_state.get("lastSeenVersion", "")
        if last_seen and last_seen < __version__:
            QTimer.singleShot(1000, self._show_whats_new)
        self.app_state["lastSeenVersion"] = __version__
        self.state_manager.save()

        # Uncomment this to pin to desktop automatically (warning: window will be unmovable by standard dragging)
        # pin_to_desktop(int(self.winId()))

    def _show_tutorial(self):
        dialog = TutorialDialog(self)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        avoid = self._window_rects_to_avoid()
        self._place_dialog_avoiding_rects(dialog, avoid)
        dialog.exec()
        if not self.app_state.get("seenTutorial"):
            self.app_state["seenTutorial"] = True
            self.state_manager.save()

    def _show_whats_new(self):
        from src.backend.updater import FRIENDLY_CHANGELOGS
        from src.frontend.whats_new_dialog import WhatsNewDialog
        changelog = FRIENDLY_CHANGELOGS.get(__version__) or self.app_state.get("lastChangelog", "Bug fixes and improvements.")
        dialog = WhatsNewDialog(changelog, self)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        avoid = self._window_rects_to_avoid()
        self._place_dialog_avoiding_rects(dialog, avoid)
        dialog.exec()

    def _screen_available_rect(self):
        screen = self.screen()
        if screen is not None:
            return screen.availableGeometry()
        from PyQt6.QtGui import QGuiApplication
        primary = QGuiApplication.primaryScreen()
        return primary.availableGeometry() if primary else None

    def _restore_window_geometry(self):
        """Apply saved size and position. Lock only blocks dragging, not restore on launch."""
        x, y, width, height = self.state_manager.get_window_geometry()
        available = self._screen_available_rect()
        min_w = self.minimumWidth() if self.minimumWidth() > 0 else MIN_WINDOW_WIDTH
        min_h = self.minimumHeight() if self.minimumHeight() > 0 else MIN_WINDOW_HEIGHT
        x, y, width, height = StateManager.clamp_geometry_to_screen(
            x, y, width, height, available, min_w, min_h
        )
        self.resize(width, height)
        self.move(x, y)

    def _persist_window_geometry(self):
        """Write current geometry to appstate (position always stored for when lock is released)."""
        self.state_manager.save_window_geometry(
            self.pos().x(),
            self.pos().y(),
            self.width(),
            self.height(),
        )
        self.app_state = self.state_manager.state

    def closeEvent(self, event):
        self._persist_window_geometry()
        self._resize_timer.stop()
        if getattr(self, '_force_quit', False):
            self._hotkey_filter.unregister_all()
            QApplication.instance().removeNativeEventFilter(self._hotkey_filter)
            if getattr(self, '_skip_close_confirm', False):
                self._tray.hide()
                super().closeEvent(event)
                from PyQt6.QtWidgets import QApplication as _app
                _app.instance().quit()
                return
            reply = QMessageBox.question(
                self,
                "Quit Nudge?",
                "Are you sure you want to quit Nudge?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._tray.hide()
                super().closeEvent(event)
                from PyQt6.QtWidgets import QApplication as _app
                _app.instance().quit()
            else:
                event.ignore()
                self._force_quit = False
            return
        event.ignore()
        self.hide()
        self._notify_tray_once("Nudge", "Still running in tray. Right-click tray icon to quit.")

    def _show_from_tray(self):
        self.show()
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _notify_tray_once(self, title: str, message: str, cooldown_ms: int = 10000):
        if getattr(self, '_tray_notified', False):
            return
        self._tray.show_message(title, message)
        self._tray_notified = True
        QTimer.singleShot(cooldown_ms, lambda: setattr(self, '_tray_notified', False))

    def _minimize_to_tray(self):
        self.hide()
        self._notify_tray_once("Nudge", "Still running in tray. Right-click tray icon to quit.")

    def _quit_from_tray(self):
        self._force_quit = True
        self._skip_close_confirm = True
        self.close()

    def apply_app_theme(self) -> None:
        """Re-apply global QSS when theme changes."""
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            return
        theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
        apply_theme_to_app(app, theme_id)
        theme = get_theme(theme_id)
        chrome_color = theme["colors"].get("chrome_icon", theme["colors"]["text"])
        self.btn_history.setIcon(QIcon(svg_to_pixmap(generate_svg_icon("history", chrome_color, 16), 16)))
        self.btn_settings.setIcon(QIcon(svg_to_pixmap(generate_svg_icon("settings", chrome_color, 16), 16)))
        for b in (self.btn_menu, self.btn_minimize, self.btn_exit):
            b.setStyleSheet("")
        refresh_glass_shells(self, theme_id)
        for w in app.topLevelWidgets():
            if w is not self and w.isVisible():
                refresh_glass_shells(w, theme_id)
        if hasattr(self, "_tray"):
            self._tray.restyle(theme)

    def apply_settings(self):
        self.app_state = self.state_manager.state
        self.task_text_size = int(self.app_state.get("taskTextSize", 14))

        self.apply_app_theme()

        self.update_keyboard_shortcuts()

        # Apply mouse glow setting
        if hasattr(self, '_glow_overlay'):
            if not self.app_state.get("mouseGlow", True):
                self._glow_overlay.hide_glow()

        # Apply Opacity
        opacity = self.app_state.get("opacity", 1.0)
        self.setWindowOpacity(opacity)
        
        reconcile_layer_settings(self.app_state)
        self.setWindowFlags(
            compose_main_window_flags(
                self.app_state.get("pinnedToDesktop", False),
                self.app_state.get("alwaysOnTop", False),
            )
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), Qt.GlobalColor.transparent)
        self.setPalette(pal)
        self._reapply_dwm_shadow_disable()
        self.show()

        if self.app_state.get("pinnedToDesktop", False):
            pin_to_desktop(int(self.winId()))
        else:
            unpin_from_desktop(int(self.winId()))

        self._restore_window_geometry()

        QTimer.singleShot(0, self.render_tasks)  # FIX-A1: window restore — full render required

    def _check_and_prompt_update(self):
        def _check():
            result = check_for_update(__version__)
            self._update_check_done.emit(result)
        t = threading.Thread(target=_check, daemon=True)
        t.start()

    def _on_update_check_done(self, result):
        if result.error:
            ThemedMessageDialog.information(self, "Update Check", f"Could not check for updates.\n\n{result.error}")
            return
        known_id = self.app_state.get("lastSeenReleaseId", 0)
        if result.available or (result.release_id and result.release_id != known_id):
            self._show_update_dialog(result)
        else:
            ThemedMessageDialog.information(self, "Update Check", "You\u2019re up to date!")

    def _show_update_dialog(self, result: UpdateCheckResult):
        friendly, _ = parse_changelog(result.changelog, result.latest_version)
        self.app_state["lastChangelog"] = friendly
        self.app_state["lastSeenReleaseId"] = result.release_id
        self.state_manager.save()
        dialog = UpdateInfoDialog(result.latest_version, friendly, result.download_url, self)
        avoid = self._window_rects_to_avoid()
        self._place_dialog_avoiding_rects(dialog, avoid)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._apply_update(result.download_url, result.latest_version)

    def _apply_update(self, download_url: str, version: str):
        from src.frontend.update_dialog import DownloadDialog
        dialog = DownloadDialog(version, download_url, self)
        avoid = self._window_rects_to_avoid()
        self._place_dialog_avoiding_rects(dialog, avoid)
        self._download_dialog = dialog
        dialog.start_download()
        dialog.show()

    def _reapply_dwm_shadow_disable(self):
        try:
            hwnd = int(self.winId())
            # Extend glass frame into entire window to eliminate non-client area
            class MARGINS(ctypes.Structure):
                _fields_ = [
                    ("cxLeftWidth", ctypes.c_int),
                    ("cxRightWidth", ctypes.c_int),
                    ("cyTopHeight", ctypes.c_int),
                    ("cyBottomHeight", ctypes.c_int),
                ]
            margins = MARGINS(-1, -1, -1, -1)  # -1 = extend into entire window
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(
                hwnd, ctypes.byref(margins)
            )
        except Exception:
            pass

    def _apply_window_layer(self):
        """Apply window layer (AoT / Pin to Desktop) without rebuilding task list."""
        from src.backend.window_layer import (compose_main_window_flags,
                                              reconcile_layer_settings)
        reconcile_layer_settings(self.app_state)
        flags = compose_main_window_flags(
            self.app_state.get("pinnedToDesktop", False),
            self.app_state.get("alwaysOnTop", False),
        )
        geo = self.geometry()
        visible = self.isVisible()
        if visible:
            self.hide()
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), Qt.GlobalColor.transparent)
        self.setPalette(pal)
        self.setGeometry(geo)
        self.show()
        QTimer.singleShot(0, self._reapply_dwm_shadow_disable)
        QTimer.singleShot(100, self._sync_task_row_text_layouts)
        self._propagate_always_on_top()

    def _propagate_always_on_top(self):
        always_on_top = self.app_state.get("alwaysOnTop", False)
        for w in QApplication.topLevelWidgets():
            if w is self or not w.isVisible():
                continue
            flags = w.windowFlags()
            if always_on_top:
                flags |= Qt.WindowType.WindowStaysOnTopHint
            else:
                flags &= ~Qt.WindowType.WindowStaysOnTopHint
            geo = w.geometry()
            w.hide()
            w.setWindowFlags(flags)
            w.setGeometry(geo)
            w.show()

    def toggle_always_on_top(self, checked: bool):
        self.app_state = self.state_manager.state
        self.app_state["alwaysOnTop"] = checked
        if checked:
            self.app_state["pinnedToDesktop"] = False
        self.state_manager.save()
        self._apply_window_layer()

    def toggle_pinned_to_desktop(self):
        self.app_state = self.state_manager.state
        self.app_state["pinnedToDesktop"] = not self.app_state.get("pinnedToDesktop", False)
        if self.app_state["pinnedToDesktop"]:
            self.app_state["alwaysOnTop"] = False
        self.state_manager.save()
        self._apply_window_layer()

    def _toggle_pin_to_desktop_from_menu(self, checked: bool):
        geo = self.geometry()
        self.app_state = self.state_manager.state
        self.app_state["pinnedToDesktop"] = checked
        if checked:
            self.app_state["alwaysOnTop"] = False
        self.state_manager.save()
        self._apply_window_layer()
        self.apply_settings()
        self.setGeometry(geo)

    def _toggle_always_on_top_via_shortcut(self):
        current = self.app_state.get("alwaysOnTop", False)
        self.toggle_always_on_top(not current)

    def _open_export_via_shortcut(self):
        # FIX-D1: suppress shortcut when text editor has focus
        focused = QApplication.focusWidget()
        if focused and focused.inherits('QLineEdit'):
            return
        self.run_export_dialog()

    def _toggle_tray_visibility(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
            self._notify_tray_once("Nudge", "Still running in tray. Right-click tray icon to quit.")
        else:
            self.show()
            self.showNormal()
            self.activateWindow()
            self.raise_()

    def _enable_resize_hover_tracking(self, root: QWidget) -> None:
        """Show resize cursors on window edges even when the pointer is over child widgets (M1)."""
        for widget in [root, *root.findChildren(QWidget)]:
            if widget.property('resize_track_installed'):  # FIX-B1: widget property instead of id() set
                continue
            widget.setMouseTracking(True)
            widget.installEventFilter(self)
            widget.setProperty('resize_track_installed', True)  # FIX-B1

    def eventFilter(self, watched, event):
        if (
            self._frameless_chrome is not None
            and event.type() == QEvent.Type.MouseMove
            and not self._frameless_chrome.is_resizing
            and not self._frameless_chrome.is_dragging
        ):
            global_pos = event.globalPosition().toPoint()
            local_pos = self.mapFromGlobal(global_pos)
            self._frameless_chrome.update_hover_cursor(local_pos)
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._frameless_chrome is not None:
            local_pos = event.position().toPoint()
            global_pos = event.globalPosition().toPoint()
            if self._frameless_chrome.handle_mouse_press(
                global_pos,
                local_pos,
                self.app_state.get("positionLocked", False),
            ):
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._frameless_chrome is not None:
            local_pos = event.position().toPoint()
            global_pos = event.globalPosition().toPoint()
            if self._frameless_chrome.handle_mouse_move(global_pos, local_pos):
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._frameless_chrome is not None:
            if self._frameless_chrome.handle_mouse_release():
                self._persist_window_geometry()
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def init_ui(self):
        self.setWindowTitle("Nudge")
        self.setWindowIcon(get_app_icon())
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self._frameless_chrome = FramelessChromeController(self)
        
        # Prepare for Liquid Glass look (Frameless and Translucent)
        # We use purely FramelessWindowHint so it appears as a standard Windows app on the taskbar.
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), Qt.GlobalColor.transparent)
        self.setPalette(pal)
        self.setMouseTracking(True)

        # Disable DWM shadow — deferred so HWND is fully created
        QTimer.singleShot(0, self._reapply_dwm_shadow_disable)
        
        central_widget = QWidget()
        central_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        
        # --- Top UI Bar (Title + Window Controls) ---
        top_bar = QHBoxLayout()
        title_label = QLabel("Nudge", self)
        set_label_point_size(title_label, 12, bold=True)
        self.title_label = title_label
        top_bar.addWidget(title_label)
        
        top_bar.addStretch()
        
        chrome_btn_sz = 28

        theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        chrome_color = theme["colors"].get("chrome_icon", theme["colors"]["text"])
        self._overflow_menu = QMenu(self)
        self._overflow_menu.setObjectName("overflowMenu")
        act_update = self._overflow_menu.addAction("Check for Updates")
        act_update.triggered.connect(self._check_and_prompt_update)
        act_feedback = self._overflow_menu.addAction("Send Feedback")
        act_feedback.triggered.connect(self._open_feedback_dialog)
        act_support = self._overflow_menu.addAction("Support Nudge")
        act_support.triggered.connect(self._open_support_dialog)
        act_whatsnew = self._overflow_menu.addAction("What\u2019s New")
        act_whatsnew.triggered.connect(self._show_whats_new)

        self.btn_menu = QPushButton("\u00b7\u00b7\u00b7")
        self.btn_menu.setObjectName("chromeButton")
        self.btn_menu.setFixedSize(chrome_btn_sz, chrome_btn_sz)
        self.btn_menu.setToolTip("More")
        self.btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_menu.clicked.connect(self._show_overflow_menu)
        top_bar.addWidget(self.btn_menu)

        self.btn_history = QPushButton()
        self.btn_history.setObjectName("chromeButton")
        self.btn_history.setIcon(QIcon(svg_to_pixmap(generate_svg_icon("history", chrome_color, 16), 16)))
        self.btn_history.setIconSize(QSize(16, 16))
        self.btn_history.setFixedSize(chrome_btn_sz, chrome_btn_sz)
        self.btn_history.setToolTip("History")
        self.btn_history.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_history.clicked.connect(self.open_history)
        top_bar.addWidget(self.btn_history)

        self.btn_settings = QPushButton()
        self.btn_settings.setObjectName("chromeButton")
        self.btn_settings.setIcon(QIcon(svg_to_pixmap(generate_svg_icon("settings", chrome_color, 16), 16)))
        self.btn_settings.setIconSize(QSize(16, 16))
        self.btn_settings.setFixedSize(chrome_btn_sz, chrome_btn_sz)
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.clicked.connect(self.open_settings)
        top_bar.addWidget(self.btn_settings)

        self.btn_minimize = QPushButton("-")
        self.btn_minimize.setObjectName("chromeButton")
        self.btn_minimize.setFixedSize(chrome_btn_sz, chrome_btn_sz)
        self.btn_minimize.setToolTip("Minimize")
        self.btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_minimize.clicked.connect(self.showMinimized)
        top_bar.addWidget(self.btn_minimize)

        self.btn_exit = QPushButton("✕")
        self.btn_exit.setObjectName("chromeButtonClose")
        self.btn_exit.setFixedSize(chrome_btn_sz, chrome_btn_sz)
        self.btn_exit.setToolTip("Close (press Escape twice)")
        self.btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exit.clicked.connect(self.close)
        top_bar.addWidget(self.btn_exit)

        layout.addLayout(top_bar)

        central_widget.setObjectName("glassPanel")
        
        # --- Group selector + new tasks input ---
        self._group_row_widgets: list[QWidget] = []
        group_row = QHBoxLayout()
        group_label = QLabel("Group:")
        set_label_point_size(group_label, 14)
        group_row.addWidget(group_label)
        self._group_row_widgets.append(group_label)

        self.group_combo = QComboBox(self)
        self.group_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        group_row.addWidget(self.group_combo, 1)
        self._group_row_widgets.append(self.group_combo)

        self.btn_add_group = QPushButton("+")
        self.btn_add_group.setObjectName("accentIconButton")
        self.btn_add_group.setFixedSize(32, 28)
        self.btn_add_group.setToolTip("Add task group")
        self.btn_add_group.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_group.clicked.connect(self._add_group_dialog)
        group_row.addWidget(self.btn_add_group)
        self._group_row_widgets.append(self.btn_add_group)
        layout.addLayout(group_row)

        self.input_bar = QLineEdit(self)
        self.input_bar.setPlaceholderText("Add tasks (split by period)...")
        self.input_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_bar.returnPressed.connect(self.process_input)
        self.input_bar.setDragEnabled(True)
        layout.addWidget(self.input_bar)

        self._input_glow = QGraphicsDropShadowEffect(self.input_bar)
        self._input_glow.setBlurRadius(20)
        self._input_glow.setOffset(0, 0)
        self._input_glow.setColor(QColor(79, 195, 247, 0))
        self.input_bar.setGraphicsEffect(self._input_glow)
        self.input_bar.installEventFilter(self)
        self._refresh_group_combo()
        
        # --- Task Checklist Layout ---
        # Scroll area for tasks
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tasks_widget = QWidget()
        self.tasks_widget.setObjectName("transparentSurface")
        self.tasks_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tasks_layout.setSpacing(6)

        self._flat_drop_indicator = QFrame(self.tasks_widget)
        self._flat_drop_indicator.setObjectName("dropIndicator")
        self._flat_drop_indicator.setFixedHeight(3)
        self._flat_drop_indicator.hide()

        self._group_drop_indicator = QFrame(self.tasks_widget)
        self._group_drop_indicator.setObjectName("dropIndicator")
        self._group_drop_indicator.setFixedHeight(3)
        self._group_drop_indicator.hide()

        self.scroll_area.setWidget(self.tasks_widget)
        layout.addWidget(self.scroll_area, stretch=1)

        self._glow_overlay = GlowOverlay(self.scroll_area.viewport())
        self._glow_overlay.setGeometry(self.scroll_area.viewport().rect())
        self.scroll_area.viewport().installEventFilter(self)

        # Empty state widget (shown when no tasks)
        self._empty_state_widget = QWidget()
        empty_layout = QVBoxLayout(self._empty_state_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(8)

        self._empty_state_label = QLabel("Add a task to get started")
        self._empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state_label.setStyleSheet("opacity: 0.5; font-size: 14px;")
        empty_layout.addWidget(self._empty_state_label)

        self._empty_state_arrow = QLabel("\u2193")
        self._empty_state_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state_arrow.setStyleSheet("font-size: 24px; opacity: 0.4;")
        empty_layout.addWidget(self._empty_state_arrow)

        self._empty_state_timer = QTimer(self)
        self._empty_state_timer.timeout.connect(self._animate_empty_arrow)
        self._empty_state_arrow_visible = True

        layout.addWidget(self._empty_state_widget)
        self._empty_state_widget.hide()

        layout.setContentsMargins(15, 15, 15, 15)

        self.setCentralWidget(central_widget)
        self._enable_resize_hover_tracking(central_widget)
        # Let the glass panel and task list grow when the user resizes the window.
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _animate_empty_arrow(self):
        self._empty_state_arrow_visible = not self._empty_state_arrow_visible
        self._empty_state_arrow.setStyleSheet(
            f"font-size: 24px; opacity: {'0.4' if self._empty_state_arrow_visible else '0.15'};"
        )

    def _update_empty_state(self):
        has_tasks = len(self.tasks) > 0
        self._empty_state_widget.setVisible(not has_tasks)
        self.scroll_area.setVisible(has_tasks)
        if not has_tasks:
            self._empty_state_timer.start(800)
        else:
            self._empty_state_timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_task_list_viewport_width()
        if hasattr(self, '_glow_overlay') and self.scroll_area is not None:
            self._glow_overlay.setGeometry(self.scroll_area.viewport().rect())
        if self._resize_timer.isActive():
            self._resize_timer.stop()
        self._resize_timer.start(100)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._reapply_dwm_shadow_disable)
        self._sync_task_list_viewport_width()
        self._sync_task_row_text_layouts()

    def _sync_task_list_viewport_width(self) -> None:
        """Rows span the scroll viewport so Edit can sit on the window's right edge."""
        if self.scroll_area is None or self.tasks_widget is None:
            return
        viewport_w = self.scroll_area.viewport().width()
        if viewport_w > 0:
            sb = self.scroll_area.verticalScrollBar()
            scrollbar_w = sb.width() if sb.isVisible() else 0
            self.tasks_widget.setMinimumWidth(viewport_w - scrollbar_w)

    def _sync_task_row_text_layouts(self):
        self._sync_task_list_viewport_width()
        if self.tasks_layout is not None:
            self.tasks_layout.activate()
        for section in self.group_sections.values():
            if hasattr(section, "force_layout"):
                section.force_layout()
        for row in self.task_row_widgets.values():
            if hasattr(row, "sync_text_layout"):
                row.sync_text_layout()

    def init_keyboard_shortcuts(self):
        self.update_keyboard_shortcuts()

    def update_keyboard_shortcuts(self):
        history_sequence = QKeySequence.fromString(self.app_state.get("historyShortcut", "Ctrl+H"), QKeySequence.SequenceFormat.PortableText)
        settings_sequence = QKeySequence.fromString(self.app_state.get("settingsShortcut", "Ctrl+,"), QKeySequence.SequenceFormat.PortableText)
        pin_sequence = QKeySequence.fromString(self.app_state.get("pinShortcut", "Ctrl+P"), QKeySequence.SequenceFormat.PortableText)
        aot_sequence = QKeySequence.fromString(self.app_state.get("alwaysOnTopShortcut", "Alt+T"), QKeySequence.SequenceFormat.PortableText)
        export_sequence = QKeySequence.fromString(self.app_state.get("exportShortcut", "Ctrl+E"), QKeySequence.SequenceFormat.PortableText)
        tray_sequence = QKeySequence.fromString(self.app_state.get("toggleTrayShortcut", "Ctrl+M"), QKeySequence.SequenceFormat.PortableText)

        if self.history_shortcut is not None:
            self.history_shortcut.setParent(None)
            self.history_shortcut.deleteLater()
        if self.settings_shortcut is not None:
            self.settings_shortcut.setParent(None)
            self.settings_shortcut.deleteLater()
        if self.pin_shortcut is not None:
            self.pin_shortcut.setParent(None)
            self.pin_shortcut.deleteLater()
        if self.always_on_top_shortcut is not None:
            self.always_on_top_shortcut.setParent(None)
            self.always_on_top_shortcut.deleteLater()
        if self.toggle_tray_shortcut is not None:
            self.toggle_tray_shortcut.setParent(None)
            self.toggle_tray_shortcut.deleteLater()
            self.toggle_tray_shortcut = None
        if self._tray_hotkey_id is not None:
            self._hotkey_filter.unregister(self._tray_hotkey_id)
            self._tray_hotkey_id = None
        if self.export_shortcut is not None:
            self.export_shortcut.setParent(None)
            self.export_shortcut.deleteLater()

        self.history_shortcut = QShortcut(history_sequence, self)
        self.history_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)  # FIX-D1: prevent theft from QLineEdit, also works when child dialogs have focus
        self.history_shortcut.activated.connect(self.open_history)

        self.settings_shortcut = QShortcut(settings_sequence, self)
        self.settings_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)  # FIX-D1
        self.settings_shortcut.activated.connect(self.open_settings)

        self.pin_shortcut = QShortcut(pin_sequence, self)
        self.pin_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.pin_shortcut.activated.connect(self.toggle_pinned_to_desktop)

        if not aot_sequence.isEmpty():
            self.always_on_top_shortcut = QShortcut(aot_sequence, self)
            self.always_on_top_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            self.always_on_top_shortcut.activated.connect(self._toggle_always_on_top_via_shortcut)

        if not tray_sequence.isEmpty():
            hid = self._hotkey_filter.register(
                self.app_state.get("toggleTrayShortcut", "Ctrl+M"),
                self._toggle_tray_visibility,
            )
            if hid is not None:
                self._tray_hotkey_id = hid

        if not export_sequence.isEmpty():
            self.export_shortcut = QShortcut(export_sequence, self)
            self.export_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)  # FIX-D1
            self.export_shortcut.activated.connect(self._open_export_via_shortcut)

    def process_input(self):
        raw_text = self.input_bar.text()
        if not raw_text.strip():
            return
        
        new_tasks = InputParser.parse_input(raw_text)
        group_id = self._current_input_group_id()
        for task in new_tasks:
            task["groupId"] = group_id
        self.tasks.extend(new_tasks)
        self.input_bar.clear()
        
        # Save to disk after modification
        self.store.save(self.tasks)
        last_row = None
        for task in new_tasks:
            last_row = self._append_task_row_widget(task)
        if last_row is not None and self.scroll_area is not None:
            QTimer.singleShot(0, lambda r=last_row: self.scroll_area.ensureWidgetVisible(r, 0, 80))

    def _current_input_group_id(self) -> str:
        group_id = self.group_combo.currentData()
        return group_id if group_id else GENERAL_GROUP_ID

    def _on_escape_pressed(self):
        if self.input_bar.hasFocus():
            self.input_bar.clear()
            return
        self._escape_count += 1
        if self._escape_count >= 2:
            self._escape_count = 0
            self._escape_timer.stop()
            self._force_quit = True
            self.close()
        else:
            self._escape_timer.start(500)

    def eventFilter(self, obj, event):
        if obj is self.scroll_area.viewport():
            if event.type() == QEvent.Type.MouseMove:
                if self.app_state.get("mouseGlow", True):
                    self._glow_overlay.setGeometry(self.scroll_area.viewport().rect())
                    self._glow_overlay.set_glow_center(event.position())
                return False
            elif event.type() == QEvent.Type.Enter:
                if self.app_state.get("mouseGlow", True):
                    self._glow_overlay.setGeometry(self.scroll_area.viewport().rect())
                return False
            elif event.type() == QEvent.Type.Leave:
                self._glow_overlay.hide_glow()
                return False
        elif obj is self.input_bar:
            if event.type() == QEvent.Type.FocusIn:
                theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
                accent = get_theme(theme_id)["colors"].get("toggle_on", "#4fc3f7")
                c = QColor(accent)
                c.setAlpha(77)
                self._input_glow.setColor(c)
                return False
            elif event.type() == QEvent.Type.FocusOut:
                self._input_glow.setColor(QColor(79, 195, 247, 0))
                return False
        elif event.type() == QEvent.Type.MouseButtonPress:
            if self.input_bar.hasFocus() and obj is not self.input_bar:
                self.input_bar.clearFocus()
        elif event.type() == QEvent.Type.DragEnter and obj is self.tasks_widget:
            if event.mimeData().hasFormat("application/x-nudge-task-row"):
                self._flat_drag_hover_index = -1
                event.acceptProposedAction()
                return True
            elif event.mimeData().hasFormat("application/x-nudge-group"):
                event.acceptProposedAction()
                return True
        elif event.type() == QEvent.Type.DragMove and obj is self.tasks_widget:
            if event.mimeData().hasFormat("application/x-nudge-task-row"):
                self._update_flat_drop_indicator(event.position().toPoint())
                event.acceptProposedAction()
                return True
            elif event.mimeData().hasFormat("application/x-nudge-group"):
                self._update_group_drop_indicator(event.position().toPoint())
                event.acceptProposedAction()
                return True
        elif event.type() == QEvent.Type.DragLeave and obj is self.tasks_widget:
            self._flat_drop_indicator.hide()
            self._group_drop_indicator.hide()
            event.accept()
            return True
        elif event.type() == QEvent.Type.Drop and obj is self.tasks_widget:
            self._flat_drop_indicator.hide()
            self._group_drop_indicator.hide()
            source = event.source()
            if source is not None and hasattr(source, "_task_ref"):
                self._on_flat_list_drop(source, event.position().toPoint())
                event.acceptProposedAction()
                return True
            elif event.mimeData().hasFormat("application/x-nudge-group"):
                self._on_group_drop(event.position().toPoint(), event.mimeData())
                event.acceptProposedAction()
                return True
        return super().eventFilter(obj, event)

    def _refresh_group_combo(self, select_group_id: str | None = None) -> None:
        if not hasattr(self, "group_combo"):
            return
        target = select_group_id or self._current_input_group_id()
        self.group_combo.blockSignals(True)
        self.group_combo.clear()
        for group in sorted_groups(self.groups_data):
            self.group_combo.addItem(group["name"], group["id"])
        index = self.group_combo.findData(target)
        if index >= 0:
            self.group_combo.setCurrentIndex(index)
        self.group_combo.blockSignals(False)

    def _save_group_expanded(self, group_id: str, expanded: bool) -> None:
        group = group_by_id(self.groups_data, group_id)
        if group is None:
            return
        group["expanded"] = expanded
        self.group_store.save(self.groups_data)

    def _select_active_group(self, group_id: str) -> None:
        if not hasattr(self, "group_combo"):
            return
        idx = self.group_combo.findData(group_id)
        if idx < 0:
            return
        if self.group_combo.currentIndex() != idx:
            self.group_combo.blockSignals(True)
            self.group_combo.setCurrentIndex(idx)
            self.group_combo.blockSignals(False)

    def _add_group_dialog(self) -> None:
        dlg = ThemedInputDialog(self, title="New Task Group", label="Group name:")
        if not dlg.exec() == QDialog.DialogCode.Accepted:
            return
        name = dlg.get_text().strip()
        if not name:
            return
        order = len(self.groups_data.get("groups", []))
        new_group = create_group(name, order)
        self.groups_data["groups"].append(new_group)
        self.group_store.save(self.groups_data)
        self._refresh_group_combo(new_group["id"])
        self.render_tasks()  # FIX-A1: group structure changed — full render required

    def _rename_group(self, group_id: str) -> None:
        group = group_by_id(self.groups_data, group_id)
        if group is None:
            return
        dlg = ThemedInputDialog(self, title="Rename Group", label="Group name:", default_text=group["name"])
        if not dlg.exec() == QDialog.DialogCode.Accepted:
            return
        name = dlg.get_text().strip()
        if not name:
            return
        group["name"] = name
        self.group_store.save(self.groups_data)
        self._refresh_group_combo(group_id)
        # FIX-A1: targeted section header update instead of full render_tasks
        section = self.group_sections.get(group_id)
        if section is not None:
            section.refresh_header_count()

    def _delete_group(self, group_id: str) -> None:
        if group_id == GENERAL_GROUP_ID:
            ThemedMessageDialog.information(self, "Cannot Delete", "The General group cannot be deleted.")
            return
        group = group_by_id(self.groups_data, group_id)
        if group is None:
            return
        count = len(tasks_for_group(self.tasks, group_id))
        message = f"Delete group \"{group['name']}\"?"
        if count:
            message += f"\n{count} task(s) will move to General."
        if not ThemedMessageDialog.question(self, "Delete Group", message, default_yes=False):
            return
        for task in self.tasks:
            if task.get("groupId") == group_id:
                task["groupId"] = GENERAL_GROUP_ID
        self.groups_data["groups"] = [g for g in self.groups_data["groups"] if g.get("id") != group_id]
        self.group_store.save(self.groups_data)
        self.store.save(self.tasks)
        self._refresh_group_combo(GENERAL_GROUP_ID)
        self.render_tasks()  # FIX-A1: group structure changed — full render required

    def _move_group_order(self, group_id: str, offset: int) -> None:
        groups = sorted_groups(self.groups_data)
        ids = [g["id"] for g in groups]
        if group_id not in ids:
            return
        index = ids.index(group_id)
        new_index = index + offset
        if new_index < 0 or new_index >= len(groups):
            return
        groups[index], groups[new_index] = groups[new_index], groups[index]
        for order, group in enumerate(groups):
            group["order"] = order
        self.groups_data["groups"] = groups
        self.group_store.save(self.groups_data)
        self.render_tasks()  # FIX-A1: group structure changed — full render required

    def _show_group_header_menu(self, group_id: str, global_pos) -> None:
        menu = QMenu(self)
        self._style_context_menu(menu)
        rename_action = QAction("Rename Group", self)
        rename_action.triggered.connect(lambda: self._rename_group(group_id))
        menu.addAction(rename_action)

        move_up = QAction("Move Group Up", self)
        move_up.triggered.connect(lambda: self._move_group_order(group_id, -1))
        menu.addAction(move_up)

        move_down = QAction("Move Group Down", self)
        move_down.triggered.connect(lambda: self._move_group_order(group_id, 1))
        menu.addAction(move_down)

        if group_id != GENERAL_GROUP_ID:
            menu.addSeparator()
            delete_action = QAction("Delete Group", self)
            delete_action.triggered.connect(lambda: self._delete_group(group_id))
            menu.addAction(delete_action)

        menu.exec(global_pos)

    def _move_task_to_group(self, task_ref: dict, target_group_id: str) -> None:
        old_group_id = task_ref.get("groupId", GENERAL_GROUP_ID)
        row = self.task_row_widgets.get(id(task_ref))
        old_section = self.group_sections.get(old_group_id)
        if old_section is not None and row is not None:
            old_section.content_layout.removeWidget(row)
            if row in old_section.task_rows:
                old_section.task_rows.remove(row)
            old_section.refresh_header_count()
        task_ref["groupId"] = target_group_id
        self.store.save(self.tasks)
        new_section = self.group_sections.get(target_group_id)
        if new_section is not None and row is not None:
            new_section.add_task_row(row)
            new_section.refresh_header_count()
        self._sync_task_row_text_layouts()

    def _tasks_in_group(self, group_id: str) -> list:
        return tasks_for_group(self.tasks, group_id, include_done=True)
        
    def render_tasks(self):
        # FIX-A1: Called only on initial load and group-structure changes.
        # Use _on_task_added / _on_task_moved for incremental updates.
        self.tasks_widget.setUpdatesEnabled(False)
        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.task_row_widgets = {}
        self.group_sections = {}

        self.task_text_size = int(self.state_manager.state.get("taskTextSize", 14))
        groups_enabled = self.app_state.get("groupsEnabled", True)

        for w in self._group_row_widgets:
            w.setVisible(groups_enabled)

        if not groups_enabled:
            self.tasks_widget.setAcceptDrops(True)
            for task in self.tasks:
                row = TaskRowWidget(
                    task["text"],
                    checked=task.get("done", False),
                    text_size=self.task_text_size,
                    on_toggled=lambda checked, t=task: self.toggle_task(t, checked),
                    on_commit=lambda new_text, t=task: self.update_task_text(t, new_text),
                    on_context_menu=lambda global_pos, t=task: self.show_task_context_menu(t),
                    content_indent=0,
                )
                self.tasks_layout.addWidget(row, 0, Qt.AlignmentFlag.AlignTop)
                row._main_window = self
                row.set_task_ref(task)
                self.task_row_widgets[id(task)] = row
        else:
            self.tasks_widget.setAcceptDrops(False)
            for group in sorted_groups(self.groups_data):
                group_id = group["id"]
                group_tasks = tasks_for_group(self.tasks, group_id)
                section = TaskGroupSection(
                    group,
                    len(group_tasks),
                    text_size=14,
                    on_toggle_expanded=self._save_group_expanded,
                    on_header_context_menu=self._show_group_header_menu,
                    on_header_clicked=self._select_active_group,
                )
                for task in group_tasks:
                    row = TaskRowWidget(
                        task["text"],
                        checked=task.get("done", False),
                        text_size=self.task_text_size,
                        on_toggled=lambda checked, t=task: self.toggle_task(t, checked),
                        on_commit=lambda new_text, t=task: self.update_task_text(t, new_text),
                        on_context_menu=lambda global_pos, t=task: self.show_task_context_menu(t),
                        content_indent=8,
                    )
                    section.add_task_row(row)
                    row._main_window = self
                    row.set_task_ref(task)
                    self.task_row_widgets[id(task)] = row
                section._main_window = self
                section.refresh_header_count()
                self.tasks_layout.addWidget(section, 0, Qt.AlignmentFlag.AlignTop)
                self.group_sections[group_id] = section

        self.tasks_layout.addStretch(1)
        self._sync_task_list_viewport_width()
        self._sync_task_row_text_layouts()
        self._flat_drop_indicator.raise_()
        self._group_drop_indicator.raise_()
        self.tasks_widget.setUpdatesEnabled(True)
        self._update_empty_state()
        import gc; gc.collect()

        central = self.centralWidget()
        if central is not None:
            self._enable_resize_hover_tracking(central)

    def _append_task_row_widget(self, task: dict) -> TaskRowWidget:
        self._sync_task_list_viewport_width()
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        groups_enabled = self.app_state.get("groupsEnabled", True)
        fresh = StateManager("appstate.json")
        fresh.load()
        text_size = int(fresh.state.get("taskTextSize", 14))
        self.state_manager.state["taskTextSize"] = text_size
        self.task_text_size = text_size
        row = TaskRowWidget(
            task["text"],
            checked=task.get("done", False),
            text_size=text_size,
            on_toggled=lambda checked, t=task: self.toggle_task(t, checked),
            on_commit=lambda new_text, t=task: self.update_task_text(t, new_text),
            on_context_menu=lambda global_pos, t=task: self.show_task_context_menu(t),
            content_indent=0 if not groups_enabled else 8,
        )
        if not groups_enabled:
            insert_before = max(0, self.tasks_layout.count() - 1)
            self.tasks_layout.insertWidget(insert_before, row, 0, Qt.AlignmentFlag.AlignTop)
        else:
            group_id = task.get("groupId", GENERAL_GROUP_ID)
            section = self.group_sections.get(group_id)
            if section is None:
                row.setParent(None)
                row.deleteLater()
                return None
            group_tasks = tasks_for_group(self.tasks, group_id)
            insert_index = len(group_tasks) - 1
            section.add_task_row(row, index=insert_index)
            section.refresh_header_count()
        row._main_window = self
        row.set_task_ref(task)
        self.task_row_widgets[id(task)] = row
        self._sync_task_list_viewport_width()
        self._sync_task_row_text_layouts()
        return row

    def _remove_task_row_widget(self, task: dict) -> None:
        row = self.task_row_widgets.pop(id(task), None)
        if row is None:
            return
        row._stop_countdown()
        groups_enabled = self.app_state.get("groupsEnabled", True)
        if groups_enabled:
            group_id = task.get("groupId", GENERAL_GROUP_ID)
            section = self.group_sections.get(group_id)
            if section is not None:
                section.remove_task_row(row)
                section.refresh_header_count()
        else:
            self.tasks_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self._sync_task_list_viewport_width()
        self._update_empty_state()

    def _style_context_menu(self, menu: QMenu) -> None:
        theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        menu.setStyleSheet(menu_stylesheet(theme))

    def show_task_context_menu(self, task_ref):
        menu = QMenu(self)
        self._style_context_menu(menu)

        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(lambda: self.edit_task(task_ref))
        menu.addAction(edit_action)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(task_ref.get("text", "")))
        menu.addAction(copy_action)

        menu.addSeparator()

        reminder_menu = menu.addMenu("Set Reminder")
        remind_15m = QAction("15 minutes", self)
        remind_15m.triggered.connect(lambda: self._set_task_reminder(task_ref, 15))
        reminder_menu.addAction(remind_15m)
        remind_30m = QAction("30 minutes", self)
        remind_30m.triggered.connect(lambda: self._set_task_reminder(task_ref, 30))
        reminder_menu.addAction(remind_30m)
        remind_1h = QAction("1 hour", self)
        remind_1h.triggered.connect(lambda: self._set_task_reminder(task_ref, 60))
        reminder_menu.addAction(remind_1h)
        remind_2h = QAction("2 hours", self)
        remind_2h.triggered.connect(lambda: self._set_task_reminder(task_ref, 120))
        reminder_menu.addAction(remind_2h)
        remind_tomorrow = QAction("Tomorrow 9:00 AM", self)
        remind_tomorrow.triggered.connect(lambda: self._set_task_reminder_at_time(task_ref, "09:00", days_ahead=1))
        reminder_menu.addAction(remind_tomorrow)
        reminder_menu.addSeparator()
        remind_custom = QAction("Custom...", self)
        remind_custom.triggered.connect(lambda: self._show_custom_reminder_dialog(task_ref))
        reminder_menu.addAction(remind_custom)
        if self._timer_manager.get_timer_for_task(task_ref["id"]) is not None:
            clear_reminder = QAction("Clear Reminder", self)
            clear_reminder.triggered.connect(lambda: self._clear_task_reminder(task_ref))
            menu.addAction(clear_reminder)

        move_top_action = QAction("Move to Top", self)
        move_top_action.triggered.connect(lambda: self.move_task_to_top(task_ref))
        menu.addAction(move_top_action)

        move_bottom_action = QAction("Move to Bottom", self)
        move_bottom_action.triggered.connect(lambda: self.move_task_to_bottom(task_ref))
        menu.addAction(move_bottom_action)

        menu.addSeparator()

        move_menu = menu.addMenu("Move to Group")
        for group in sorted_groups(self.groups_data):
            action = QAction(group["name"], self)
            gid = group["id"]
            action.triggered.connect(lambda checked=False, g=gid: self._move_task_to_group(task_ref, g))
            move_menu.addAction(action)
        
        menu.addSeparator()

        delete_action = QAction("Delete", self)
        delete_action.setObjectName("deleteAction")
        delete_action.triggered.connect(lambda: self.delete_task(task_ref))
        menu.addAction(delete_action)

        # Calculate menu height and clamp position to screen bounds
        pos = QCursor.pos()
        screen = QApplication.screenAt(pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # Estimate menu height: action count * row height + padding
        action_count = len(menu.actions())
        row_height = 28  # Approximate height per menu item
        menu_height = action_count * row_height + 8  # 8px for padding
        menu_width = 200  # Approximate menu width
        
        # Clamp x position
        x = pos.x()
        if x + menu_width > screen_rect.right():
            x = screen_rect.right() - menu_width
        if x < screen_rect.left():
            x = screen_rect.left()
        
        # Clamp y position
        y = pos.y()
        if y + menu_height > screen_rect.bottom():
            y = screen_rect.bottom() - menu_height
        if y < screen_rect.top():
            y = screen_rect.top()
        
        menu.exec(QPoint(x, y))

    def edit_task(self, task_ref):
        row = self.task_row_widgets.get(id(task_ref))
        if row is not None:
            row.begin_edit()

    def update_task_text(self, task_ref, new_text):
        task_ref["text"] = new_text
        self.store.save(self.tasks)

    def _reorder_task(self, task_ref, new_idx):
        """Move task to new_idx within its group (or flat list)."""
        group_id = task_ref.get("groupId", GENERAL_GROUP_ID)
        groups_enabled = self.app_state.get("groupsEnabled", True)
        if groups_enabled:
            group_tasks = self._tasks_in_group(group_id)
            if task_ref not in group_tasks:
                return
            idx = group_tasks.index(task_ref)
            if idx == new_idx:
                return
            group_tasks.insert(new_idx, group_tasks.pop(idx))
            self.tasks = rebuild_tasks_preserving_groups(self.tasks, self.groups_data, group_id, group_tasks)
            section = self.group_sections.get(group_id)
            row = self.task_row_widgets.get(id(task_ref))
            if section is not None and row is not None:
                section.content_layout.removeWidget(row)
                if row in section.task_rows:
                    section.task_rows.remove(row)
                section.add_task_row(row, index=new_idx)
                section.refresh_header_count()
        else:
            if task_ref not in self.tasks:
                return
            idx = self.tasks.index(task_ref)
            if idx == new_idx:
                return
            self.tasks.insert(new_idx, self.tasks.pop(idx))
            row = self.task_row_widgets.get(id(task_ref))
            if row is not None:
                self.tasks_layout.removeWidget(row)
                self.tasks_layout.insertWidget(new_idx, row, 0, Qt.AlignmentFlag.AlignTop)
        self.store.save(self.tasks)
        self._sync_task_row_text_layouts()

    def move_task(self, task_ref, offset):
        group_id = task_ref.get("groupId", GENERAL_GROUP_ID)
        groups_enabled = self.app_state.get("groupsEnabled", True)
        if groups_enabled:
            group_tasks = self._tasks_in_group(group_id)
            if task_ref not in group_tasks:
                return
            idx = group_tasks.index(task_ref)
            new_idx = idx + offset
            if 0 <= new_idx < len(group_tasks):
                self._reorder_task(task_ref, new_idx)
        else:
            if task_ref not in self.tasks:
                return
            idx = self.tasks.index(task_ref)
            new_idx = idx + offset
            if 0 <= new_idx < len(self.tasks):
                self._reorder_task(task_ref, new_idx)

    def move_task_to_top(self, task_ref):
        self._reorder_task(task_ref, 0)

    def move_task_to_bottom(self, task_ref):
        group_id = task_ref.get("groupId", GENERAL_GROUP_ID)
        groups_enabled = self.app_state.get("groupsEnabled", True)
        if groups_enabled:
            group_tasks = self._tasks_in_group(group_id)
            self._reorder_task(task_ref, len(group_tasks) - 1)
        else:
            self._reorder_task(task_ref, len(self.tasks) - 1)

    def _on_flat_list_drop(self, row_widget, pos: QPoint) -> None:
        task_ref = getattr(row_widget, "_task_ref", None)
        if task_ref is None or task_ref not in self.tasks:
            return
        old_idx = self.tasks.index(task_ref)
        other_widgets = []
        for i in range(self.tasks_layout.count()):
            item = self.tasks_layout.itemAt(i)
            w = item.widget() if item is not None else None
            if w is not None and w is not row_widget and hasattr(w, "_task_ref") and not w.isHidden():
                other_widgets.append(w)
        insert_idx = len(other_widgets)
        for i, w in enumerate(other_widgets):
            if pos.y() < w.y() + w.height() // 2:
                insert_idx = i
                break
        if insert_idx < 0 or insert_idx == old_idx:
            return
        self.tasks_layout.removeWidget(row_widget)
        if insert_idx < len(other_widgets):
            target = other_widgets[insert_idx]
            li = self.tasks_layout.indexOf(target)
            self.tasks_layout.insertWidget(li, row_widget, 0, Qt.AlignmentFlag.AlignTop)
        else:
            li = self._layout_stretch_index()
            if li >= 0:
                self.tasks_layout.insertWidget(li, row_widget, 0, Qt.AlignmentFlag.AlignTop)
            else:
                self.tasks_layout.addWidget(row_widget, 0, Qt.AlignmentFlag.AlignTop)
        self.tasks.pop(old_idx)
        self.tasks.insert(insert_idx, task_ref)
        self.store.save(self.tasks)
        self._sync_task_row_text_layouts()

    def _layout_stretch_index(self) -> int:
        for i in range(self.tasks_layout.count()):
            item = self.tasks_layout.itemAt(i)
            if item is not None and item.widget() is None and item.spacerItem() is not None:
                return i
        return -1

    def _update_flat_drop_indicator(self, pos: QPoint) -> None:
        visible = []
        for i in range(self.tasks_layout.count()):
            item = self.tasks_layout.itemAt(i)
            w = item.widget() if item is not None else None
            if w is not None and hasattr(w, "_task_ref") and not w.isHidden():
                visible.append(w)
        if not visible:
            self._flat_drop_indicator.hide()
            return
        insert_idx = len(visible)
        for i, w in enumerate(visible):
            if pos.y() < w.y() + w.height() // 2:
                insert_idx = i
                break
        y_pos = 0
        if insert_idx < len(visible):
            y_pos = visible[insert_idx].y() - 1
        else:
            y_pos = visible[-1].y() + visible[-1].height() - 1
        self._flat_drop_indicator.move(0, max(0, y_pos))
        self._flat_drop_indicator.setFixedWidth(self.tasks_widget.width())
        self._flat_drop_indicator.show()

    def _update_group_drop_indicator(self, pos: QPoint) -> None:
        from src.frontend.task_group_section import TaskGroupSection
        sections = []
        for i in range(self.tasks_layout.count()):
            item = self.tasks_layout.itemAt(i)
            w = item.widget() if item is not None else None
            if isinstance(w, TaskGroupSection) and not w.isHidden():
                sections.append(w)
        if not sections:
            self._group_drop_indicator.hide()
            return
        insert_idx = len(sections)
        for i, s in enumerate(sections):
            if pos.y() < s.y() + s.height() // 2:
                insert_idx = i
                break
        y_pos = 0
        if insert_idx < len(sections):
            y_pos = sections[insert_idx].y() - 1
        else:
            y_pos = sections[-1].y() + sections[-1].height() - 1
        self._group_drop_indicator.move(0, max(0, y_pos))
        self._group_drop_indicator.setFixedWidth(self.tasks_widget.width())
        self._group_drop_indicator.show()

    def _on_group_drop(self, pos: QPoint, mime_data) -> None:
        self._group_drop_indicator.hide()
        group_id_bytes = mime_data.data("application/x-nudge-group").data()
        if not group_id_bytes:
            return
        source_id = group_id_bytes.decode()
        from src.frontend.task_group_section import TaskGroupSection
        sections = []
        for i in range(self.tasks_layout.count()):
            item = self.tasks_layout.itemAt(i)
            w = item.widget() if item is not None else None
            if isinstance(w, TaskGroupSection) and not w.isHidden():
                sections.append(w)
        target_idx = len(sections)
        for i, s in enumerate(sections):
            if pos.y() < s.y() + s.height() // 2:
                target_idx = i
                break
        groups = self.groups_data.get("groups", [])
        src_idx = next((i for i, g in enumerate(groups) if g["id"] == source_id), -1)
        if src_idx < 0:
            return
        if src_idx == target_idx or (src_idx < target_idx and target_idx - 1 == src_idx):
            return
        group = groups.pop(src_idx)
        if target_idx > src_idx:
            target_idx -= 1
        groups.insert(target_idx, group)
        for i, g in enumerate(groups):
            g["order"] = i
        self.group_store.save(self.groups_data)
        self.render_tasks()

    def _on_row_dropped(self, row_widget, target_group_id, insert_index):
        task_ref = getattr(row_widget, "_task_ref", None)
        if task_ref is None:
            return
        old_group_id = task_ref.get("groupId", GENERAL_GROUP_ID)
        if old_group_id == target_group_id:
            group_tasks = self._tasks_in_group(old_group_id)
            if task_ref not in group_tasks:
                return
            idx = group_tasks.index(task_ref)
            if idx == insert_index or insert_index < 0:
                return
            if insert_index > idx:
                insert_index -= 1
            group_tasks.insert(insert_index, group_tasks.pop(idx))
            self.tasks = rebuild_tasks_preserving_groups(self.tasks, self.groups_data, old_group_id, group_tasks)
            self.store.save(self.tasks)
            section = self.group_sections.get(old_group_id)
            if section is not None:
                section.content_layout.removeWidget(row_widget)
                if row_widget in section.task_rows:
                    section.task_rows.remove(row_widget)
                section.add_task_row(row_widget, index=insert_index)
                section.refresh_header_count()
        else:
            old_section = self.group_sections.get(old_group_id)
            if old_section is not None:
                old_section.content_layout.removeWidget(row_widget)
                if row_widget in old_section.task_rows:
                    old_section.task_rows.remove(row_widget)
                old_section.refresh_header_count()
            task_ref["groupId"] = target_group_id
            self.store.save(self.tasks)
            new_section = self.group_sections.get(target_group_id)
            if new_section is not None:
                new_section.add_task_row(row_widget, index=insert_index)
                new_section.refresh_header_count()
        self._sync_task_row_text_layouts()

    def delete_task(self, task_ref):
        if not ThemedMessageDialog.question(self, "Delete Task", "Are you sure you want to delete this task? This cannot be undone."):
            return
        if task_ref in self.tasks:
            self._timer_manager.cancel_task_reminder(task_ref["id"])
            self.tasks.remove(task_ref)
            self.store.save(self.tasks)
            self._remove_task_row_widget(task_ref)

    def toggle_task(self, task_ref, is_checked):
        task_ref["done"] = is_checked
        if is_checked:
            self.archive_task(task_ref)
            return

        self.store.save(self.tasks)

    def archive_task(self, task_ref):
        if task_ref not in self.tasks:
            return

        self._timer_manager.cancel_task_reminder(task_ref["id"])
        original_index = self.tasks.index(task_ref)

        archived_task = dict(task_ref)
        archived_task["done"] = True
        archived_task["completedAt"] = datetime.now().isoformat()

        self.history_store.append_and_save(archived_task)  # FIX-B2: atomic append

        self.tasks.remove(task_ref)
        self.store.save(self.tasks)
        self._remove_task_row_widget(task_ref)
        if self._history_dialog is not None:
            self._history_dialog.add_external_archived_task(archived_task)

        archived_task["_archivedFromIndex"] = original_index
        self._last_archived_task = archived_task
        self._show_undo_toast(task_ref.get("text", "Task"))

    def _show_undo_toast(self, task_text):
        toast = UndoToast(self, f"Completed: {task_text}", self._undo_last_archive)
        toast.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
        )
        toast._apply_theme()
        toast._reposition()
        toast.show()
        toast.raise_()

    def _undo_last_archive(self):
        task = self._last_archived_task
        if task is None:
            return
        self._last_archived_task = None
        self.restore_task_from_history(task)

    def migrate_completed_tasks_to_history(self):
        completed = [task for task in self.tasks if task.get("done", False)]
        if not completed:
            return

        history = self.history_store.load()
        for task in completed:
            archived_task = dict(task)
            archived_task["done"] = True
            archived_task.setdefault("completedAt", datetime.now().isoformat())
            history.append(archived_task)

        self.history_store.save(history)
        self.tasks = [task for task in self.tasks if not task.get("done", False)]
        self.store.save(self.tasks)

    def restore_task_from_history(self, task_ref):
        original_index = task_ref.pop("_archivedFromIndex", None)

        history = self.history_store.load()
        if task_ref in history:
            history.remove(task_ref)
            self.history_store.save(history)

        restored_task = dict(task_ref)
        restored_task["done"] = False
        restored_task.pop("completedAt", None)
        for key in ("reminderAt", "reminderFired", "reminderRepeat"):
            restored_task.pop(key, None)

        if original_index is not None and 0 <= original_index <= len(self.tasks):
            self.tasks.insert(original_index, restored_task)
        else:
            self.tasks.append(restored_task)

        self.store.save(self.tasks)
        self.render_tasks()

    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        self._style_context_menu(context_menu)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        context_menu.addAction(settings_action)

        always_on_top_action = QAction("Always on Top", self)
        always_on_top_action.setCheckable(True)
        always_on_top_action.setChecked(self.app_state.get("alwaysOnTop", False))
        always_on_top_action.triggered.connect(self.toggle_always_on_top)
        context_menu.addAction(always_on_top_action)

        pin_desktop_action = QAction("Pin to Desktop Background", self)
        pin_desktop_action.setCheckable(True)
        pin_desktop_action.setChecked(self.app_state.get("pinnedToDesktop", False))
        pin_desktop_action.triggered.connect(self._toggle_pin_to_desktop_from_menu)
        context_menu.addAction(pin_desktop_action)

        context_menu.addSeparator()
        
        clear_action = QAction("Clear Completed Tasks", self)
        clear_action.triggered.connect(self.clear_completed_tasks)
        context_menu.addAction(clear_action)
        
        exit_action = QAction("Exit App", self)
        exit_action.triggered.connect(self.close)
        context_menu.addAction(exit_action)
        
        context_menu.exec(event.globalPos())

    def clear_completed_tasks(self):
        completed = [t for t in self.tasks if t.get("done", False)]
        if not completed:
            return
        if not ThemedMessageDialog.question(self, "Clear Completed Tasks", "Are you sure you want to clear all completed tasks? They will be moved to history."):
            return

        # Save completed tasks to history
        history = self.history_store.load()
        for task in completed:
            archived_task = dict(task)
            archived_task["done"] = True
            archived_task["completedAt"] = datetime.now().isoformat()
            history.append(archived_task)
        self.history_store.save(history)

        self.tasks = [t for t in self.tasks if not t.get("done", False)]
        self.store.save(self.tasks)
        self.render_tasks()  # FIX-A1: clear completed — many tasks affected, full render OK

    def _place_dialog_near_geometry(
        self,
        dialog: QDialog,
        ref_geom,
        *,
        y_offset: int = 0,
        prefer_right: bool = False,
    ) -> None:
        """Place a dialog beside a reference rect, clamped to the screen work area (H6)."""
        screen = self.screen()
        available = screen.availableGeometry() if screen else ref_geom

        if dialog.width() <= 0 or dialog.height() <= 0:
            dialog.adjustSize()

        gap = 15
        dialog_w = dialog.width()
        dialog_h = dialog.height()
        left_x = ref_geom.left() - dialog_w - gap
        right_x = ref_geom.right() + gap

        fits_left = left_x >= available.left()
        fits_right = right_x + dialog_w <= available.right()

        if prefer_right:
            if fits_right:
                target_x = right_x
            elif fits_left:
                target_x = left_x
            else:
                target_x = max(
                    available.left(),
                    min(ref_geom.left(), available.right() - dialog_w),
                )
        else:
            if fits_left:
                target_x = left_x
            elif fits_right:
                target_x = right_x
            else:
                target_x = max(
                    available.left(),
                    available.right() - dialog_w,
                )

        target_y = max(
            available.top(),
            min(ref_geom.top() + y_offset, available.bottom() - dialog_h),
        )
        dialog.move(target_x, target_y)

    def _place_dialog_near_main_window(self, dialog: QDialog, *, y_offset: int = 0) -> None:
        """Place a dialog beside the main window, clamped to the screen work area (H6)."""
        self._place_dialog_near_geometry(dialog, self.geometry(), y_offset=y_offset)

    def _window_rects_to_avoid(self, extra: QDialog | None = None) -> list:
        """Rects export must not overlap: main window plus any open side panel."""
        rects = [self.frameGeometry()]
        if extra is not None:
            rects.append(extra.frameGeometry())
        elif self._active_side_dialog is not None:
            rects.append(self._active_side_dialog.frameGeometry())
        return rects

    def _place_dialog_avoiding_rects(
        self,
        dialog: QDialog,
        avoid_rects: list,
        *,
        y_offset: int = 0,
        gap: int = 15,
    ) -> None:
        """Place dialog beside app windows without overlapping them (H6b)."""
        if not avoid_rects:
            self._place_dialog_near_main_window(dialog, y_offset=y_offset)
            return

        screen = self.screen()
        available = screen.availableGeometry() if screen else avoid_rects[0]

        if dialog.width() <= 0 or dialog.height() <= 0:
            dialog.adjustSize()

        dialog_w = dialog.width()
        dialog_h = dialog.height()

        union = avoid_rects[0]
        for rect in avoid_rects[1:]:
            union = union.united(rect)

        candidates = [
            (union.right() + gap, union.top() + y_offset),
            (union.left() - gap - dialog_w, union.top() + y_offset),
            (union.right() + gap, union.bottom() - dialog_h),
            (union.left() - gap - dialog_w, union.bottom() - dialog_h),
            (union.left(), union.top() - gap - dialog_h),
            (union.left(), union.bottom() + gap),
        ]

        def overlaps(x: int, y: int) -> bool:
            dlg_rect = QRect(x, y, dialog_w, dialog_h)
            for rect in avoid_rects:
                padded = rect.adjusted(-gap, -gap, gap, gap)
                if dlg_rect.intersects(padded):
                    return True
            return False

        for x, y in candidates:
            x = max(available.left(), min(x, available.right() - dialog_w))
            y = max(available.top(), min(y, available.bottom() - dialog_h))
            if not overlaps(x, y):
                dialog.move(x, y)
                return

        self._place_dialog_near_geometry(dialog, union, y_offset=y_offset, prefer_right=True)

    def _run_side_dialog(self, dialog: QDialog) -> None:
        """Show a non-modal side panel and track it for export avoidance."""
        self._active_side_dialog = dialog
        dialog.finished.connect(lambda r, d=dialog: self._on_side_dialog_closed(d))
        dialog.show()

    def _on_side_dialog_closed(self, dialog: QDialog) -> None:
        if self._active_side_dialog is dialog:
            self._active_side_dialog = None
        if self._history_dialog is dialog:
            self._history_dialog = None
        if self._settings_dialog is dialog:
            self._settings_dialog = None
        if self._export_dialog is dialog:
            self._export_dialog = None
        dialog.deleteLater()

    def open_history(self):
        # FIX-D1: suppress shortcut when text editor has focus
        focused = QApplication.focusWidget()
        if focused and focused.inherits('QLineEdit'):
            return
        if self._history_dialog is not None:
            self._history_dialog.close()
            return
        dialog = HistoryDialog(
            self.history_store,
            self.restore_task_from_history,
            self.groups_data,
            self,
            self.state_manager,
        )
        self._history_dialog = dialog
        avoid = self._window_rects_to_avoid()
        self._place_dialog_avoiding_rects(dialog, avoid)
        self._run_side_dialog(dialog)

    def open_settings(self):
        # FIX-D1: suppress shortcut when text editor has focus
        focused = QApplication.focusWidget()
        if focused and focused.inherits('QLineEdit'):
            return
        if self._settings_dialog is not None:
            self._settings_dialog.close()
            return
        dialog = SettingsDialog(self.state_manager, self)
        self._settings_dialog = dialog
        avoid = self._window_rects_to_avoid()
        self._place_dialog_avoiding_rects(dialog, avoid)
        self._run_side_dialog(dialog)

    def _on_timer_fired(self, timer_id: str, name: str):
        cfg = self._timer_manager._timers.get(timer_id)
        if cfg is not None and cfg.task_id is not None:
            task = next((t for t in self.tasks if t["id"] == cfg.task_id), None)
            if task is not None:
                task_text = task.get("text", name)
                self._tray.show_message("Nudge", f"Reminder: {task_text}")
                row = self.task_row_widgets.get(id(task))
                if row is not None:
                    row.set_task_ref(task)
            else:
                self._timer_manager.cancel_task_reminder(cfg.task_id)
        else:
            self._tray.show_message("Nudge", f"Reminder: {name}")
        self.app_state["timers"] = self._timer_manager.to_list()
        self.state_manager.save()

    def _migrate_task_reminders(self) -> None:
        """One-time migration: move task reminder fields from tasks.json into TimerManager."""
        has_reminders = any(t.get("reminderAt") for t in self.tasks)
        if not has_reminders:
            return
        for task in self.tasks:
            reminder_str = task.get("reminderAt")
            if not reminder_str:
                continue
            try:
                reminder_dt = datetime.fromisoformat(reminder_str)
            except (ValueError, TypeError):
                for key in ("reminderAt", "reminderFired", "reminderRepeat"):
                    task.pop(key, None)
                continue
            repeat = task.get("reminderRepeat", 0)
            self._timer_manager.add_task_reminder(
                task_id=task["id"],
                name=task.get("text", "Task reminder"),
                trigger_at=reminder_dt,
                repeat_minutes=repeat,
            )
            for key in ("reminderAt", "reminderFired", "reminderRepeat"):
                task.pop(key, None)
        self.store.save(self.tasks)

    def _open_reminders(self):
        from src.frontend.timer_dialog import TimerDialog
        dialog = TimerDialog(self._timer_manager, self)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.finished.connect(self._on_reminders_closed)
        dialog.show()

    def _on_reminders_closed(self):
        self.app_state["timers"] = self._timer_manager.to_list()
        self.state_manager.save()

    def _set_task_reminder(self, task_ref, minutes_from_now: int, repeat: int = 0):
        trigger_at = datetime.now() + timedelta(minutes=minutes_from_now)
        self._timer_manager.cancel_task_reminder(task_ref["id"])
        self._timer_manager.add_task_reminder(
            task_id=task_ref["id"],
            name=task_ref.get("text", "Task reminder"),
            trigger_at=trigger_at,
            repeat_minutes=repeat,
        )
        self.app_state["timers"] = self._timer_manager.to_list()
        self.state_manager.save()
        row = self.task_row_widgets.get(id(task_ref))
        if row is not None:
            row.set_task_ref(task_ref)

    def _set_task_reminder_at_time(self, task_ref, time_str: str, days_ahead: int = 0):
        now = datetime.now()
        parts = time_str.split(":")
        target = now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0, microsecond=0)
        if days_ahead > 0:
            target += timedelta(days=days_ahead)
        if target <= now:
            target += timedelta(days=1)
        self._timer_manager.cancel_task_reminder(task_ref["id"])
        self._timer_manager.add_task_reminder(
            task_id=task_ref["id"],
            name=task_ref.get("text", "Task reminder"),
            trigger_at=target,
            repeat_minutes=0,
        )
        self.app_state["timers"] = self._timer_manager.to_list()
        self.state_manager.save()
        row = self.task_row_widgets.get(id(task_ref))
        if row is not None:
            row.set_task_ref(task_ref)

    def _clear_task_reminder(self, task_ref):
        self._timer_manager.cancel_task_reminder(task_ref["id"])
        self.app_state["timers"] = self._timer_manager.to_list()
        self.state_manager.save()
        row = self.task_row_widgets.get(id(task_ref))
        if row is not None:
            row.set_task_ref(task_ref)

    def _show_custom_reminder_dialog(self, task_ref):
        from PyQt6.QtCore import QDate, QTime

        theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)

        dlg = QDialog(self)
        dlg.setWindowTitle("Set Reminder \u2014 Nudge")
        dlg.resize(420, 320)
        dlg.setMinimumSize(380, 280)
        dlg.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dlg._drag_pos = None

        frame = QFrame(dlg)
        frame.setObjectName("glassPanel")
        frame.setGeometry(0, 0, 420, 320)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(6)

        title = QLabel("Set Reminder")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        # -- Current reminder label (6.1: read-only display of existing reminder) --
        current_reminder_label = None
        existing_cfg = self._timer_manager.get_timer_for_task(task_ref["id"])
        if existing_cfg is not None:
            existing_dt = datetime.fromtimestamp(existing_cfg.next_trigger_at)
            current_reminder_label = QLabel(f"Current reminder: {existing_dt.strftime('%A, %d %b %Y at %H:%M')}")
            current_reminder_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,120); font-style: italic;")
            current_reminder_label.setWordWrap(True)
            layout.addWidget(current_reminder_label)

        # -- Quick presets row --
        presets_label = QLabel("Quick set:")
        presets_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,160);")
        layout.addWidget(presets_label)

        duration_row = QHBoxLayout()
        duration_row.setSpacing(6)
        duration_input = QLineEdit()
        duration_input.setPlaceholderText("e.g. 25 minutes, 2 hours, 3 days...")
        duration_input.setMinimumWidth(180)
        duration_row.addWidget(duration_input, 1)
        duration_apply = QPushButton("Set")
        duration_apply.setObjectName("ghostButton")
        duration_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        duration_apply.setFixedSize(50, 26)
        duration_row.addWidget(duration_apply)
        layout.addLayout(duration_row)

        # 6.3: Explanatory label for quick-set
        quickset_hint = QLabel("Type a shortcut or use the pickers above \u2014 both update together.")
        quickset_hint.setStyleSheet("font-size: 10px; color: rgba(255,255,255,100);")
        layout.addWidget(quickset_hint)

        # -- Date and time row --
        dt_label = QLabel("When:")
        dt_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,160);")
        layout.addWidget(dt_label)

        dt_row = QHBoxLayout()
        dt_row.setSpacing(8)

        # 6.1: Pre-populate with existing reminder or default to tomorrow 9:00 AM
        existing_cfg = self._timer_manager.get_timer_for_task(task_ref["id"])
        if existing_cfg is not None:
            existing_dt = datetime.fromtimestamp(existing_cfg.next_trigger_at)
            initial_date = QDate(existing_dt.year, existing_dt.month, existing_dt.day)
            initial_time = QTime(existing_dt.hour, existing_dt.minute)
        else:
            initial_date = QDate.currentDate().addDays(1)
            initial_time = QTime(9, 0)

        date_edit = QDateEdit(initial_date)
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("MMM d, yyyy")
        date_edit.setMinimumDate(QDate.currentDate())
        date_edit.setMinimumWidth(130)
        dt_row.addWidget(date_edit)

        time_edit = QTimeEdit(initial_time)
        time_edit.setDisplayFormat("hh:mm AP")
        time_edit.setMinimumWidth(90)
        dt_row.addWidget(time_edit)

        dt_row.addStretch()
        layout.addLayout(dt_row)

        # 6.2: Live preview label
        preview_label = QLabel()
        preview_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,180); font-weight: 500;")
        preview_label.setWordWrap(True)
        layout.addWidget(preview_label)

        # Store the computed target datetime (with seconds) for duration-based setting
        _computed_target = [None]

        # 6.2: Confirmation label (initially hidden)
        confirm_label = QLabel()
        confirm_label.setStyleSheet("font-size: 11px; color: #4ade80; font-weight: 600;")
        confirm_label.hide()
        layout.addWidget(confirm_label)

        # -- Repeat section --
        repeat_row = QHBoxLayout()
        repeat_row.setSpacing(6)
        repeat_cb = QCheckBox("Repeat every")
        repeat_row.addWidget(repeat_cb)

        repeat_spin = QSpinBox()
        repeat_spin.setRange(1, 1440)
        repeat_spin.setValue(30)
        repeat_spin.setSuffix(" min")
        repeat_spin.setFixedWidth(90)
        repeat_spin.setEnabled(False)
        repeat_cb.toggled.connect(repeat_spin.setEnabled)
        repeat_row.addWidget(repeat_spin)
        repeat_row.addStretch()
        layout.addLayout(repeat_row)

        layout.addStretch()

        # -- Button row --
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedHeight(28)
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)
        set_btn = QPushButton("Set")
        set_btn.setObjectName("primaryButton")
        set_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        set_btn.setFixedHeight(28)
        set_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(set_btn)
        layout.addLayout(btn_row)

        # 6.2: Update preview label function
        def _update_preview():
            q_date = date_edit.date()
            q_time = time_edit.time()
            target = datetime(q_date.year(), q_date.month(), q_date.day(),
                              q_time.hour(), q_time.minute())
            preview_label.setText(f"Will remind at: {target.strftime('%A, %d %b %Y at %H:%M')}")

        def _on_picker_changed(_):
            _computed_target[0] = None
            _update_preview()

        date_edit.dateChanged.connect(_on_picker_changed)
        time_edit.timeChanged.connect(_on_picker_changed)
        _update_preview()

        # -- Duration input handler --
        import re as _re

        def _parse_duration():
            text = duration_input.text().strip().lower()
            if not text:
                return
            match = _re.match(r"(\d+)\s*(m|min|mins|minutes|h|hr|hrs|hours|d|day|days)?", text)
            if not match:
                return
            amount = int(match.group(1))
            unit = (match.group(2) or "m").lower()
            if unit in ("d", "day", "days"):
                delta = timedelta(days=amount)
            elif unit in ("h", "hr", "hrs", "hours", "hour"):
                delta = timedelta(hours=amount)
            else:
                delta = timedelta(minutes=amount)
            target = datetime.now() + delta
            _computed_target[0] = target
            date_edit.setDate(QDate(target.year, target.month, target.day))
            time_edit.setTime(QTime(target.hour, target.minute))
            _update_preview()

        # 6.3: Real-time sync from quick-set input to pickers
        duration_input.textChanged.connect(lambda _: _parse_duration())
        duration_apply.clicked.connect(_parse_duration)
        duration_input.returnPressed.connect(_parse_duration)

        # -- Drag / resize / overlap --
        def _resize(e):
            frame.setGeometry(dlg.rect())
        dlg.resizeEvent = _resize

        def _mouse_press(e):
            if e.button() == Qt.MouseButton.LeftButton:
                dlg._drag_pos = e.globalPosition().toPoint()
                e.accept()
        dlg.mousePressEvent = _mouse_press

        def _mouse_move(e):
            if dlg._drag_pos is not None and e.buttons() == Qt.MouseButton.LeftButton:
                dlg.move(dlg.pos() + e.globalPosition().toPoint() - dlg._drag_pos)
                dlg._drag_pos = e.globalPosition().toPoint()
                e.accept()
        dlg.mouseMoveEvent = _mouse_move

        def _key_press(e):
            if e.key() == Qt.Key.Key_Escape:
                dlg.reject()
                e.accept()
            elif e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                dlg.accept()
                e.accept()
            else:
                QDialog.keyPressEvent(dlg, e)
        dlg.keyPressEvent = _key_press

        # -- Place dialog avoiding main window --
        avoid = self._window_rects_to_avoid()
        self._place_dialog_avoiding_rects(dlg, avoid)

        refresh_glass_shells(dlg, theme_id)

        if dlg.exec():
            if _computed_target[0] is not None:
                reminder_dt = _computed_target[0]
                _computed_target[0] = None
            else:
                q_date = date_edit.date()
                q_time = time_edit.time()
                reminder_dt = datetime(
                    q_date.year(), q_date.month(), q_date.day(),
                    q_time.hour(), q_time.minute(), q_time.second(),
                )
            if reminder_dt <= datetime.now():
                from PyQt6.QtWidgets import QMessageBox as _MB
                _MB.warning(dlg, "Invalid Time", "Reminder time must be in the future.")
                return
            self._timer_manager.cancel_task_reminder(task_ref["id"])
            self._timer_manager.add_task_reminder(
                task_id=task_ref["id"],
                name=task_ref.get("text", "Task reminder"),
                trigger_at=reminder_dt,
                repeat_minutes=repeat_spin.value() if repeat_cb.isChecked() else 0,
            )
            self.app_state["timers"] = self._timer_manager.to_list()
            self.state_manager.save()
            row = self.task_row_widgets.get(id(task_ref))
            if row is not None:
                row.set_task_ref(task_ref)

    def _show_overflow_menu(self):
        self._style_overflow_menu()
        self._overflow_menu.exec(self.btn_menu.mapToGlobal(QPoint(0, self.btn_menu.height())))

    def _style_overflow_menu(self):
        theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        bg = theme["colors"].get("surface", "#1e1e1e")
        fg = theme["colors"].get("text", "#ffffff")
        border = theme["colors"].get("border", "rgba(255,255,255,40)")
        self._overflow_menu.setStyleSheet(f"""
            QMenu {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 4px 0;
            }}
            QMenu::item {{
                padding: 6px 24px;
            }}
            QMenu::item:selected {{
                background: rgba(255,255,255,30);
            }}
        """)

    def _open_support_dialog(self):
        from src.frontend.support_dialog import SupportDialog
        dialog = SupportDialog(self)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._place_dialog_avoiding_rects(dialog, self._window_rects_to_avoid())
        dialog.exec()

    def _open_feedback_dialog(self):
        import json
        from urllib.parse import quote
        state_text = json.dumps(self.app_state, indent=2)
        dialog = FeedbackDialog(self, state_text)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            feedback = dialog.feedback_text() or "(no comment)"
            body = "\n".join([
                "App: Nudge",
                "Version: 1.0",
                "",
                "--- My Feedback ---",
                feedback,
                "",
                "--- App State ---",
                state_text,
            ])
            subject = "Feedback: Nudge"
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(body)
            gmail_uri = (
                f"https://mail.google.com/mail/u/0/?view=cm&fs=1"
                f"&to=nudgefeedback@gmail.com"
                f"&su={quote(subject)}"
                f"&body={quote(body)}"
            )
            open_url(gmail_uri)
            if not opened:
                ThemedMessageDialog.information(
                    self,
                    "Feedback Copied",
                    "Could not open Gmail in your browser. The feedback text has "
                    "been copied to your clipboard. Please paste it into an email "
                    "to nudgefeedback@gmail.com",
                )

    def run_export_dialog(self, anchor: QDialog | None = None):
        if self._export_dialog is not None:
            self._export_dialog.close()
            return

        from src.frontend.export_dialog import ExportDialog

        dialog = ExportDialog(self, self)
        self._export_dialog = dialog
        avoid = self._window_rects_to_avoid(anchor)
        self._place_dialog_avoiding_rects(dialog, avoid)
        dialog.finished.connect(lambda r, d=dialog: self._on_side_dialog_closed(d))
        dialog.show()



