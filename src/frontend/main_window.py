import ctypes
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from PyQt6.QtCore import (QEvent, QPoint, QPointF, QRect, QSize, Qt, QTimer,
                          pyqtSignal)
from PyQt6.QtGui import (QAction, QBrush, QColor, QCursor, QIcon, QKeySequence,
                         QPainter, QPixmap, QRadialGradient, QShortcut)
from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateEdit,
                             QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QMenu, QPushButton, QScrollArea,
                             QSizePolicy, QSpinBox, QTimeEdit, QVBoxLayout,
                             QWidget)

from src import __version__
from src.backend.boot_checker import BootChecker
from src.backend.defaults import (DEFAULT_GROUPS_ENABLED,
                                  DEFAULT_HISTORY_RETENTION_DAYS,
                                  DEFAULT_SHOW_BOOT_NOTIFICATION)
from src.backend.group_store import GroupStore
from src.backend.icon import get_app_icon
from src.backend.input_parser import InputParser
from src.backend.recurrence_manager import RecurrenceManager
from src.backend.state_manager import StateManager
from src.backend.task_groups import (GENERAL_GROUP_ID, create_group,
                                     group_by_id, migrate_tasks_group_ids,
                                     rebuild_tasks_preserving_groups,
                                     sorted_groups, tasks_for_group)
from src.backend.task_store import TaskStore
from src.backend.updater import UpdateCheckResult, normalize_update_check_url, parse_changelog
from src.backend.update_client import UpdateClient
from src.backend.window_geometry import (DEFAULT_WINDOW_HEIGHT,
                                         DEFAULT_WINDOW_WIDTH,
                                         MIN_WINDOW_HEIGHT, MIN_WINDOW_WIDTH)
from src.backend.window_layer import (compose_main_window_flags,
                                      reconcile_layer_settings)
from src.frontend.context_menu_builder import ContextMenuBuilder, MenuContext
from src.constants import (ADD_GROUP_BTN_SIZE, CENTRAL_WIDGET_MARGINS,
                           CENTRAL_WIDGET_SPACING, DEFERRED_RENDER_MS,
                           DWM_SHADOW_DISABLE_DELAY_MS,
                           DWM_SHADOW_DISABLE_SECOND_MS, DROP_INDICATOR_HEIGHT,
                           EMPTY_STATE_BLINK_MS, EMPTY_STATE_SPACING,
                           ESCAPE_PRESS_THRESHOLD, FOOTER_MARGINS, FOOTER_SPACING,
                           FONT_SIZE_EMPTY_STATE_ARROW, FONT_SIZE_LABEL_MD,
                           FONT_SIZE_TITLE_MD, GLOW_CORE_RATIO, GLOW_HIDDEN_X,
                           GLOW_INNER_STOP_1, GLOW_INNER_STOP_2, GLOW_INNER_STOP_3,
                           GLOW_OUTER_STOP_1, GLOW_OUTER_STOP_2, GLOW_OUTER_STOP_3,
                           GLOW_RADIUS, HISTORY_BTN_ICON_SIZE, OPACITY_DIM,
                           OPACITY_FULL, OPACITY_ICONS, RESIZE_DEBOUNCE_MS,
                           SECONDS_PER_DAY, SETTINGS_ICON_SIZE,
                           TASKS_LAYOUT_SPACING)
from src.frontend.dim_overlay import DimOverlay
from src.frontend.dialog_manager import DialogManager
from src.frontend.feedback_dialog import FeedbackDialog
from src.frontend.frameless_chrome import FramelessChromeController
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.drop_indicator import DropIndicatorOverlay
from src.frontend.group_controller import GroupContext, GroupController
from src.frontend.history_dialog import HistoryDialog
from src.frontend.hotkey_filter import GlobalHotkeyFilter
from src.frontend.settings_dialog import SettingsDialog
from src.frontend.shortcut_manager import ShortcutManager
from src.frontend.tag_filter_dropdown import TagFilterDropdown
from src.frontend.task_controller import TaskContext, TaskController
from src.frontend.task_search_bar import TaskSearchBar
from src.frontend.task_group_section import TaskGroupSection
from src.frontend.task_row import TaskRowWidget
from src.frontend.theme import (_c, apply_theme_to_app,
                                footer_history_button_stylesheet,
                                generate_svg_icon, get_theme, menu_stylesheet,
                                normalize_theme_id, overflow_menu_stylesheet,
                                refresh_glass_shells, search_icon_pixmap,
                                svg_to_pixmap)
from src.frontend.themed_input_dialog import ThemedInputDialog
from src.frontend.themed_message_dialog import ThemedMessageDialog
from src.frontend.tutorial_dialog import TutorialDialog
from src.frontend.undo_toast import UndoToast
from src.frontend.update_dialog import (DownloadDialog, InstallReadyDialog,
                                        UpdateInfoDialog)
from src.frontend.utils import set_label_point_size
from src.frontend.widget_context import WidgetContext
from src.os_layer.desktop_pin import (allow_next_minimize, pin_to_desktop,
                                      unpin_from_desktop)
from src.os_layer.platform_utils import open_url
from src.os_layer.system_tray import SystemTrayManager


class GlowOverlay(QWidget):
    """Transparent overlay that paints a glass shine following the mouse."""

    def __init__(self, parent=None):
        
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._center = QPointF(GLOW_HIDDEN_X, GLOW_HIDDEN_X)
        self._radius = GLOW_RADIUS
        self._visible = False
        self._theme_id = "dark"

    def set_theme_id(self, theme_id: str) -> None:
        self._theme_id = normalize_theme_id(theme_id)

    def set_glow_center(self, point: QPointF):
        # Skip mouse glow on light / OLED — white radial reads as noise
        if self._theme_id in ("light", "oled"):
            self.hide_glow()
            return
        self._center = point
        self._visible = True
        self.update()

    def hide_glow(self):
        self._visible = False
        self._center = QPointF(GLOW_HIDDEN_X, GLOW_HIDDEN_X)
        self.update()

    def paintEvent(self, event):
        if not self._visible:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Inner core — bright, tight
        inner = QRadialGradient(self._center, self._radius * GLOW_CORE_RATIO)
        inner.setColorAt(0, QColor(255, 255, 255, GLOW_INNER_STOP_1))
        inner.setColorAt(0.6, QColor(255, 255, 255, GLOW_INNER_STOP_2))
        inner.setColorAt(1, QColor(255, 255, 255, GLOW_INNER_STOP_3))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(inner))
        painter.drawEllipse(self._center, self._radius * GLOW_CORE_RATIO, self._radius * GLOW_CORE_RATIO)

        # Outer halo — soft, wide
        outer = QRadialGradient(self._center, self._radius)
        outer.setColorAt(0, QColor(255, 255, 255, GLOW_OUTER_STOP_1))
        outer.setColorAt(0.5, QColor(255, 255, 255, GLOW_OUTER_STOP_2))
        outer.setColorAt(1, QColor(255, 255, 255, GLOW_OUTER_STOP_3))
        painter.setBrush(QBrush(outer))
        painter.drawEllipse(self._center, self._radius, self._radius)

        painter.end()






class MainWindow(QMainWindow):
    theme_applied = pyqtSignal(str)

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
        
        # Initialize State Manager
        self.state_manager = StateManager("appstate.json")
        self.app_state = self.state_manager.load()
        if self.app_state.get("pinnedToDesktop") and self.app_state.get("alwaysOnTop"):
            reconcile_layer_settings(self.app_state)
            self.state_manager.save()
        # Apply OS theme on first launch or when followOsTheme is enabled
        if self.app_state.get("followOsTheme", True):
            from src.backend.state_manager import detect_os_theme
            os_theme = detect_os_theme()
            self.app_state["theme"] = os_theme
        self.task_text_size = int(self.app_state.get("taskTextSize", 14))
        self.title_label = None
        self._tray_hotkey_id = None
        self.task_row_widgets = {}
        self._dialog_manager = DialogManager(self)
        self._shortcut_manager = ShortcutManager(self)
        self._escape_count = 0
        self._escape_timer = QTimer(self)
        self._escape_timer.setSingleShot(True)
        self._escape_timer.timeout.connect(lambda: setattr(self, '_escape_count', 0))
        self._last_archived_task = None
        self._active_undo_toast = None
        self._pin_allow_minimize = False
        self._tray_toggle_at = 0.0

        self._hotkey_filter = GlobalHotkeyFilter()
        QApplication.instance().installNativeEventFilter(self._hotkey_filter)
        self._hotkey_filter.theme_changed.connect(self._on_os_theme_changed, Qt.ConnectionType.QueuedConnection)
        self._hotkey_registered_on_show = False

        self._theme_poll_timer = QTimer(self)
        self._theme_poll_timer.timeout.connect(self._on_theme_poll)
        self._theme_poll_timer.start(3000)

        self._escape_sc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._escape_sc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self._escape_sc.activated.connect(self._on_escape_pressed)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._on_resize_settled)
        self._resize_live = False

        self.init_ui()
        from PyQt6.QtWidgets import QApplication as _QA
        _QA.instance().installEventFilter(self)
        self._restore_window_geometry()
        # Bind hotkeys to this HWND before first registration (NULL-hwnd
        # registration is what broke tray toggle after the v2 refactor).
        self._hotkey_filter.set_hwnd(int(self.winId()))
        self._shortcut_manager.register_all()
        
        # Check for lingering tasks from yesterday and notify
        if self.app_state.get("showBootNotification", DEFAULT_SHOW_BOOT_NOTIFICATION):
            BootChecker.check_and_notify(self.tasks)

        # Purge history tasks older than the retention period
        self._purge_old_history()

        # Apply flags/theme/geometry while still hidden — show() happens in main.py
        # after controllers + first render, so DWM never paints a wrong-sized frame.
        self.apply_settings(show_window=False)

        # Ensure DWM shadow is disabled after the window is fully shown
        QTimer.singleShot(DWM_SHADOW_DISABLE_DELAY_MS, self._reapply_dwm_shadow_disable)
        QTimer.singleShot(DWM_SHADOW_DISABLE_SECOND_MS, self._reapply_dwm_shadow_disable)

        # Thread-safe update check result handler
        self._update_client = UpdateClient(self)
        self._update_client.check_finished.connect(self._on_update_check_done)

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
        self._tray.quick_add_requested.connect(self._tray_quick_add)
        self.app_state["timers"] = self._timer_manager.to_list()

        # WidgetContext — used by child widgets instead of a MainWindow back-reference
        self._widget_context = self._create_widget_context()

        # SoundManager — plays task completion sounds
        from src.frontend.sound_manager import SoundManager
        self._sound_manager = SoundManager(self.state_manager)

        # TaskController — extracted task CRUD, drag-drop, undo, metadata
        self._task_ctx = TaskContext(
            tasks=self.tasks,
            store=self.store,
            history_store=self.history_store,
            group_store=self.group_store,
            app_state=self.app_state,
            state_manager=self.state_manager,
            timer_manager=self._timer_manager,
            widget_context=self._widget_context,
            tasks_layout=self.tasks_layout,
            tasks_widget=self.tasks_widget,
            scroll_area=self.scroll_area,
            task_row_widgets=self.task_row_widgets,
            group_sections=self.group_sections,
            groups_data=self.groups_data,
            input_bar=self.input_bar,
            flat_drop_indicator=self._flat_drop_indicator,
            group_drop_indicator=self._group_drop_indicator,
            on_render_tasks=self.render_tasks,
            on_update_empty_state=self._update_empty_state,
            on_update_tag_filter=self._update_tag_filter,
            on_apply_tag_filter=self._apply_tag_filter,
            on_apply_search_filter=self._apply_search_filter,
            on_sync_viewport_width=self._sync_task_list_viewport_width,
            on_sync_row_text_layouts=self._sync_task_row_text_layouts,
            on_enable_resize_hover=self._enable_resize_hover_tracking,
            group_combo=self.group_combo,
            main_window=self,
            sound_manager=self._sound_manager,
            on_show_context_menu=self.show_task_context_menu,
            on_save_group_expanded=self._save_group_expanded,
            on_show_group_header_menu=self._show_group_header_menu,
            on_select_active_group=self._select_active_group,
        )
        self._task_controller = TaskController(self._task_ctx)
        # First paint of the task list while still hidden (main.py shows the window).
        self._task_controller.render_tasks(force=True)
        self.migrate_completed_tasks_to_history()

        # GroupController — extracted group CRUD, combo, menu, move
        self._group_ctx = GroupContext(
            main_window=self,
            groups_data=self.groups_data,
            group_store=self.group_store,
            store=self.store,
            tasks=self.tasks,
            group_combo=self.group_combo,
            group_sections=self.group_sections,
            task_row_widgets=self.task_row_widgets,
            on_render_tasks=self.render_tasks,
            on_refresh_group_combo=self._refresh_group_combo,
            on_sync_task_row_text_layouts=self._sync_task_row_text_layouts,
            on_style_context_menu=self._style_context_menu,
            app_state=self.app_state,
        )
        self._group_controller = GroupController(self._group_ctx)
        self._refresh_group_combo()

        # ContextMenuBuilder — extracted task/app context menus
        self._menu_ctx = MenuContext(
            app_state=self.app_state,
            timer_manager=self._timer_manager,
            groups_data=self.groups_data,
            bold_font=self._bold_font,
            main_widget=self,
            on_edit_task=self._task_controller.edit_task,
            on_delete_task=self._task_controller.delete_task,
            on_set_reminder=self._task_controller._set_task_reminder,
            on_set_reminder_at_time=self._task_controller._set_task_reminder_at_time,
            on_clear_reminder=self._task_controller._clear_task_reminder,
            on_show_custom_reminder=self._task_controller._show_custom_reminder_dialog,
            on_set_due_date=self._task_controller._set_task_due_date,
            on_clear_due_date=self._task_controller._clear_task_due_date,
            on_show_custom_due_date=self._task_controller._show_custom_due_date_dialog,
            on_set_priority=self._task_controller._set_task_priority,
            on_clear_priority=self._task_controller._clear_task_priority,
            on_set_recurrence=self._task_controller._set_task_recurrence,
            on_clear_recurrence=self._task_controller._clear_task_recurrence,
            on_show_custom_recurrence=self._task_controller._show_custom_recurrence_dialog,
            on_move_to_top=self._task_controller.move_task_to_top,
            on_move_to_bottom=self._task_controller.move_task_to_bottom,
            on_move_to_group=self._group_controller._move_task_to_group,
            on_open_settings=self.open_settings,
            on_toggle_always_on_top=self.toggle_always_on_top,
            on_toggle_pin=self._toggle_pin_to_desktop_from_menu,
            on_clear_completed=self._task_controller.clear_completed_tasks,
            on_close=self.close,
            style_menu=self._style_context_menu,
        )
        self._menu_builder = ContextMenuBuilder(self._menu_ctx)

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

    def _create_widget_context(self) -> WidgetContext:
        """Create a WidgetContext that child widgets use instead of a MainWindow back-reference."""
        main_win = self

        class _Ctx:
            def get_theme_id(self) -> str:
                return normalize_theme_id(main_win.app_state.get("theme", "dark"))

            def is_groups_enabled(self) -> bool:
                return main_win.app_state.get("groupsEnabled", True)

            def get_tasks_widget(self):
                return main_win.tasks_widget

            def get_tasks(self) -> list[dict]:
                return main_win.tasks

            def save_tasks(self, tasks: list[dict]) -> None:
                main_win.store.save(tasks)

            def get_timer_for_task(self, task_id: str):
                return main_win._timer_manager.get_timer_for_task(task_id) if hasattr(main_win, '_timer_manager') else None

            def update_group_drop_indicator(self, pos) -> None:
                main_win._update_group_drop_indicator(pos)

            def hide_group_drop_indicator(self) -> None:
                main_win._group_drop_indicator.hide()

            def on_group_drop(self, pos, mime_data) -> None:
                main_win._on_group_drop(pos, mime_data)

            def on_row_dropped(self, source_id: str, target_group_id: str, insert_index: int) -> None:
                main_win._on_row_dropped(source_id, target_group_id, insert_index)

        return _Ctx()

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
        self.state_manager.flush()
        self.app_state = self.state_manager.state

    def closeEvent(self, event):
        self._persist_window_geometry()
        self.store.flush()
        self.history_store.flush()
        self.group_store.flush()
        self._resize_timer.stop()
        if self._resize_live and self.tasks_widget is not None:
            self.tasks_widget.setUpdatesEnabled(True)
            self._resize_live = False
        if getattr(self, '_force_quit', False):
            self._hotkey_filter.unregister_all()
            QApplication.instance().removeNativeEventFilter(self._hotkey_filter)
            if getattr(self, '_skip_close_confirm', False):
                self._tray.hide()
                super().closeEvent(event)
                from PyQt6.QtWidgets import QApplication as _app
                _app.instance().quit()
                return
            reply = ThemedMessageDialog.question(
                self,
                "Quit Nudge?",
                "Are you sure you want to quit Nudge?",
                yes_label="Yes",
                no_label="No",
                default_yes=False,
            )
            if reply:
                self._tray.hide()
                super().closeEvent(event)
                from PyQt6.QtWidgets import QApplication as _app
                _app.instance().quit()
            else:
                event.ignore()
                self._force_quit = False
            return
        event.ignore()
        if self.app_state.get("pinnedToDesktop", False):
            unpin_from_desktop(int(self.winId()))
        self.hide()
        self._notify_tray_once("Nudge", "Still running in tray. Right-click tray icon to quit.")

    def _toggle_tray_visibility(self):
        # Global hotkey + Qt shortcut can both fire for the same keypress;
        # debounce so we only toggle once. Defer off the native-event stack.
        now = time.monotonic()
        last = getattr(self, "_tray_toggle_at", 0.0)
        if now - last < 0.2:
            return
        self._tray_toggle_at = now
        QTimer.singleShot(0, self._do_toggle_tray_visibility)

    def _do_toggle_tray_visibility(self):
        logging.info(
            "Tray toggle: visible=%s minimized=%s pinned=%s",
            self.isVisible(),
            self.isMinimized(),
            self.app_state.get("pinnedToDesktop", False),
        )
        if self.isVisible() and not self.isMinimized():
            # Release desktop pin before hide — the Win32 owner/hook must not
            # fight intentional tray hide.
            if self.app_state.get("pinnedToDesktop", False):
                unpin_from_desktop(int(self.winId()))
            self.hide()
            self._notify_tray_once("Nudge", "Still running in tray. Right-click tray icon to quit.")
        else:
            self.show()
            self.showNormal()
            self.activateWindow()
            self.raise_()
            self._sync_hotkey_hwnd()
            if self.app_state.get("pinnedToDesktop", False):
                pin_to_desktop(int(self.winId()))

    def _minimize_to_tray(self):
        if self.app_state.get("pinnedToDesktop", False):
            unpin_from_desktop(int(self.winId()))
        self.hide()
        self._notify_tray_once("Nudge", "Still running in tray. Right-click tray icon to quit.")

    def _show_from_tray(self):
        self.show()
        self.showNormal()
        self.activateWindow()
        self.raise_()
        if self.app_state.get("pinnedToDesktop", False):
            pin_to_desktop(int(self.winId()))

    def _notify_tray_once(self, title: str, message: str, cooldown_ms: int = 10000):
        if getattr(self, '_tray_notified', False):
            return
        self._tray.show_message(title, message)
        self._tray_notified = True
        QTimer.singleShot(cooldown_ms, lambda: setattr(self, '_tray_notified', False))

    def _quit_from_tray(self):
        self._force_quit = True
        self._skip_close_confirm = True
        self.close()

    def _tray_quick_add(self) -> None:
        from src.frontend.tray_quick_add_dialog import TrayQuickAddDialog
        dlg = TrayQuickAddDialog(
            groups_data=self.groups_data,
            group_store=self.group_store,
            active_group_id=self._group_controller._current_input_group_id(),
            app_state=self.app_state,
            parent=None,
        )
        dlg.accepted.connect(lambda: self._on_tray_quick_add_accepted(dlg))
        dlg.show()

    def _on_tray_quick_add_accepted(self, dlg) -> None:
        text = dlg.get_text().strip()
        if not text:
            return
        group_id = dlg.get_selected_group_id()
        idx = self.group_combo.findData(group_id)
        if idx >= 0:
            self.group_combo.blockSignals(True)
            self.group_combo.setCurrentIndex(idx)
            self.group_combo.blockSignals(False)
        saved = self.input_bar.text()
        self.input_bar.setText(text)
        self._task_controller.process_input()
        self.input_bar.setText(saved)
        self._tray.show_message("Nudge", "Task added")

    def _on_os_theme_changed(self):
        if not self.app_state.get("followOsTheme", True):
            return
        # Windows broadcasts WM_THEMECHANGED before updating the registry, so
        # defer the registry read 500ms to get the correct value.
        QTimer.singleShot(500, self._delayed_apply_os_theme)

    def _delayed_apply_os_theme(self):
        from src.backend.state_manager import detect_os_theme
        new_theme = detect_os_theme()
        if new_theme == self.app_state.get("theme"):
            return
        self.app_state["theme"] = new_theme
        self.state_manager.state["theme"] = new_theme
        self.state_manager.save()
        self.apply_app_theme()

    def _on_theme_poll(self):
        if not self.app_state.get("followOsTheme", True):
            return
        from src.backend.state_manager import detect_os_theme
        detected = detect_os_theme()
        current = self.app_state.get("theme", "dark")
        if detected != current:
            self.app_state["theme"] = detected
            self.state_manager.state["theme"] = detected
            self.state_manager.save()
            self.apply_app_theme()

    def apply_app_theme(self) -> None:
        """Re-apply global QSS when theme changes."""
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            return
        theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
        if getattr(self, "_applied_theme_id", None) == theme_id:
            # Still refresh open dialogs that asked for a theme echo.
            self.theme_applied.emit(theme_id)
            return
        self._applied_theme_id = theme_id
        apply_theme_to_app(app, theme_id)
        TaskRowWidget._checkbox_style_cache.clear()
        theme = get_theme(theme_id)
        chrome_color = theme["colors"].get("chrome_icon", theme["colors"]["text"])
        if hasattr(self, '_glow_overlay'):
            self._glow_overlay.set_theme_id(theme_id)
        if hasattr(self, 'btn_settings'):
            self.btn_settings.setIcon(QIcon(svg_to_pixmap(generate_svg_icon("settings", chrome_color, SETTINGS_ICON_SIZE), SETTINGS_ICON_SIZE)))
        # Inline search icon on the add-task field (same amber asset as search bar)
        if hasattr(self, '_search_action') and self._search_action is not None:
            self._search_action.setIcon(QIcon(search_icon_pixmap(theme, 16)))
        if hasattr(self, '_group_folder_icon') and self._group_folder_icon is not None:
            self._group_folder_icon.setPixmap(
                svg_to_pixmap(generate_svg_icon("folder", chrome_color, 16), 16)
            )
        if hasattr(self, 'btn_collapse_groups') and self.btn_collapse_groups is not None:
            self.btn_collapse_groups.setIcon(
                QIcon(svg_to_pixmap(generate_svg_icon("chevron_right", chrome_color, 14), 14))
            )
        if hasattr(self, 'btn_expand_focused') and self.btn_expand_focused is not None:
            self.btn_expand_focused.setIcon(
                QIcon(svg_to_pixmap(generate_svg_icon("chevron_down", chrome_color, 14), 14))
            )
        if hasattr(self, '_dim_overlay'):
            self._dim_overlay.apply_theme(theme)
        # Update footer history button icon
        if hasattr(self, '_footer_history_btn'):
            self._footer_history_btn.setIcon(QIcon(svg_to_pixmap(generate_svg_icon("history", chrome_color, HISTORY_BTN_ICON_SIZE), HISTORY_BTN_ICON_SIZE)))
            self._footer_history_btn.setStyleSheet(footer_history_button_stylesheet(theme))
        # Update footer task count color for current theme
        if hasattr(self, '_footer_task_count'):
            self._footer_task_count.setStyleSheet(
                f"font-size: {FONT_SIZE_LABEL_MD}px; color: {theme['colors'].get('text_muted', 'rgba(255,255,255,180)')}; background: transparent; border: none;"
            )
        # Update footer separator color for current theme
        if hasattr(self, '_footer_separator'):
            self._footer_separator.setStyleSheet(
                f"background: {theme['colors'].get('border', 'rgba(255,255,255,60)')}; border: none;"
            )
        for b in (self.btn_menu, self.btn_minimize, self.btn_exit):
            if b is not None:
                b.setStyleSheet("")
        refresh_glass_shells(self, theme_id)
        if hasattr(self, "_tray"):
            self._tray.restyle(theme)

        # Update tag filter theme
        if hasattr(self, "_tag_filter"):
            self._tag_filter.update_theme(theme_id)

        # Apply theme to search bar
        if hasattr(self, "_search_bar"):
            self._search_bar.apply_theme(theme)

        # Let the UI paint the new app QSS before per-row / dialog polish.
        QApplication.processEvents()
        self.theme_applied.emit(theme_id)

        # Defer O(rows) work so settings stays responsive.
        QTimer.singleShot(0, lambda tid=theme_id: self._finish_theme_apply(tid))

    def _finish_theme_apply(self, theme_id: str) -> None:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            for w in app.topLevelWidgets():
                if w is not self and w.isVisible():
                    refresh_glass_shells(w, theme_id)
            self._fix_line_edit_cursors(app)
        self._refresh_task_row_themes(theme_id)

    def _refresh_task_row_themes(self, theme_id: str | None = None) -> None:
        """Re-apply per-row styles that use inline colors (due dates, badges, etc.)."""
        if not hasattr(self, "task_row_widgets"):
            return
        if theme_id is None:
            theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
        for row in self.task_row_widgets.values():
            row.update_theme(theme_id)
        # Refresh group header chevrons (accent when expanded)
        if hasattr(self, "group_sections"):
            for section in self.group_sections.values():
                if hasattr(section, "update_theme"):
                    section.update_theme(theme_id)
        # Update priority header widgets and dividers in flat list
        theme = get_theme(theme_id)
        divider_color = theme["colors"].get("priority_divider", "rgba(245, 166, 35, 60)")
        for i in range(self.tasks_layout.count()):
            item = self.tasks_layout.itemAt(i)
            if item is None:
                continue
            w = item.widget()
            if w is None:
                continue
            if hasattr(w, 'update_theme') and w.__class__.__name__ == 'PriorityHeaderWidget':
                w.update_theme(theme_id)
            elif w.__class__.__name__ == 'QFrame' and w.frameShape() == QFrame.Shape.HLine:
                w.setStyleSheet(f"background: {divider_color}; border: none;")
        # Update drop overlay theme
        if hasattr(self, '_drop_overlay'):
            self._drop_overlay.update_theme(theme_id)

    def apply_settings(self, show_window: bool = True):
        self.app_state = self.state_manager.state
        self.task_text_size = int(self.app_state.get("taskTextSize", 14))

        self.apply_app_theme()

        self.update_keyboard_shortcuts()

        # Apply mouse glow setting
        if hasattr(self, '_glow_overlay'):
            self._glow_overlay.set_theme_id(
                normalize_theme_id(self.app_state.get("theme", "dark"))
            )
            if not self.app_state.get("mouseGlow", True):
                self._glow_overlay.hide_glow()

        # Apply Opacity
        opacity = self.app_state.get("opacity", 1.0)
        self.setWindowOpacity(opacity)

        reconcile_layer_settings(self.app_state)
        was_visible = self.isVisible()
        saved_geo = self.geometry() if was_visible else None
        if was_visible:
            self.hide()
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

        # Geometry must be final before the first paint. Showing first then
        # moving (old order) left translucent DWM ghost frames on screen.
        if saved_geo is not None:
            self.setGeometry(saved_geo)
        else:
            self._restore_window_geometry()

        self._reapply_dwm_shadow_disable()

        # setWindowFlags recreates the HWND — rebind Win32 hotkeys + pin hook.
        self._sync_hotkey_hwnd()
        if self.app_state.get("pinnedToDesktop", False):
            pin_to_desktop(int(self.winId()))
        else:
            unpin_from_desktop(int(self.winId()))

        if show_window:
            self.show()

        QTimer.singleShot(DEFERRED_RENDER_MS, self.render_tasks)  # FIX-A1: window restore — full render required
        self._propagate_always_on_top()

    def _check_and_prompt_update(self):
        url = normalize_update_check_url(self.app_state.get("updateCheckUrl"))
        self._update_client.start_check(__version__, url)

    def _on_update_check_done(self, result):
        if result.error:
            ThemedMessageDialog.information(self, "Update Check", f"Could not check for updates.\n\n{result.error}")
            return
        known_id = self.app_state.get("lastSeenReleaseId", 0)
        if result.available or (result.release_id and result.release_id != known_id):
            cached_version = self.app_state.get("cachedDownloadVersion", "")
            cached_path = self.app_state.get("cachedDownloadPath", "")
            if (cached_version == result.latest_version
                    and cached_path
                    and Path(cached_path).exists()):
                self._show_install_prompt(cached_path, result.latest_version, from_cache=True)
            else:
                self.app_state["cachedDownloadVersion"] = ""
                self.app_state["cachedDownloadPath"] = ""
                self.state_manager.save()
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
        self._update_info_dialog = dialog
        dialog.accepted.connect(
            lambda: self._apply_update(
                result.download_url,
                result.latest_version,
                result.asset_kind,
            )
        )
        dialog.show()

    def _apply_update(self, download_url: str, version: str, asset_kind: str = ""):
        cached_path = self.app_state.get("cachedDownloadPath", "")
        cached_version = self.app_state.get("cachedDownloadVersion", "")
        if (cached_version == version
                and cached_path
                and Path(cached_path).exists()):
            self._show_install_prompt(cached_path, version, from_cache=True)
            return
        dialog = DownloadDialog(version, download_url, asset_kind, self)
        avoid = self._window_rects_to_avoid()
        self._place_dialog_avoiding_rects(dialog, avoid)
        self._download_dialog = dialog
        dialog.download_ready.connect(lambda path, v: self._show_install_prompt(path, v))
        dialog.start_download()
        dialog.show()

    def _show_install_prompt(self, path: str, version: str, from_cache: bool = False):
        dialog = InstallReadyDialog(version, from_cache=from_cache, parent=self)
        avoid = self._window_rects_to_avoid()
        self._place_dialog_avoiding_rects(dialog, avoid)
        self._install_ready_dialog = dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.app_state["cachedDownloadVersion"] = ""
            self.app_state["cachedDownloadPath"] = ""
            self.state_manager.save()
            import sys

            from src.backend.updater import _install_update
            if getattr(sys, "frozen", False):
                _install_update(Path(path), Path(sys.executable))
                self._skip_close_confirm = True
                self._force_quit = True
                self.close()
        else:
            self.app_state["cachedDownloadVersion"] = version
            self.app_state["cachedDownloadPath"] = path
            self.state_manager.save()

    def _reapply_dwm_shadow_disable(self):
        try:
            hwnd = int(self.winId())
            class MARGINS(ctypes.Structure):
                _fields_ = [
                    ("cxLeftWidth", ctypes.c_int),
                    ("cxRightWidth", ctypes.c_int),
                    ("cyTopHeight", ctypes.c_int),
                    ("cyBottomHeight", ctypes.c_int),
                ]
            margins = MARGINS(-1, -1, -1, -1)
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(
                hwnd, ctypes.byref(margins)
            )
        except Exception as e:
            logging.warning("DWM shadow disable failed: %s", e)

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
        # setWindowFlags recreates the HWND — rebind hotkeys and pin hook.
        self._sync_hotkey_hwnd()
        if self.app_state.get("pinnedToDesktop", False):
            pin_to_desktop(int(self.winId()))
        else:
            unpin_from_desktop(int(self.winId()))
        QTimer.singleShot(DEFERRED_RENDER_MS, self._reapply_dwm_shadow_disable)
        QTimer.singleShot(RESIZE_DEBOUNCE_MS, self._sync_task_row_text_layouts)
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
        self.setGeometry(geo)

    def _toggle_always_on_top_via_shortcut(self):
        current = self.app_state.get("alwaysOnTop", False)
        self.toggle_always_on_top(not current)

    def _open_export_via_shortcut(self):
        # FIX-D1: suppress shortcut only when our own input bar has focus
        focused = QApplication.focusWidget()
        if focused is getattr(self, 'input_bar', None):
            return
        self.run_export_dialog()

    def _toggle_groups_via_shortcut(self):
        """Toggle task groups on/off via keyboard shortcut."""
        current = self.app_state.get("groupsEnabled", True)
        self.app_state["groupsEnabled"] = not current
        self.state_manager.save()
        for w in self._group_row_widgets:
            w.setVisible(self.app_state["groupsEnabled"])
        self.render_tasks()

    def _enable_resize_hover_tracking(self, root: QWidget) -> None:
        """Show resize cursors on window edges even when the pointer is over child widgets (M1)."""
        for widget in [root, *root.findChildren(QWidget)]:
            if widget.property('resize_track_installed'):  # FIX-B1: widget property instead of id() set
                continue
            widget.setMouseTracking(True)
            widget.installEventFilter(self)
            widget.setProperty('resize_track_installed', True)  # FIX-B1

    def showMinimized(self):
        if self.app_state.get("pinnedToDesktop", False):
            self._pin_allow_minimize = True
            allow_next_minimize(int(self.winId()))
        super().showMinimized()

    def changeEvent(self, event):
        # Qt-level safety net: if Show Desktop minimizes us while pinned,
        # restore immediately (Win32 hook may miss some shell paths).
        if (
            event.type() == QEvent.Type.WindowStateChange
            and self.app_state.get("pinnedToDesktop", False)
            and bool(self.windowState() & Qt.WindowState.WindowMinimized)
        ):
            if getattr(self, "_pin_allow_minimize", False):
                self._pin_allow_minimize = False
            else:
                self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
                pin_to_desktop(int(self.winId()))
        super().changeEvent(event)

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
            was_resizing = self._frameless_chrome.is_resizing
            if self._frameless_chrome.handle_mouse_release():
                if was_resizing:
                    self._on_resize_settled()
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
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), Qt.GlobalColor.transparent)
        self.setPalette(pal)
        self.setMouseTracking(True)

        # Disable DWM shadow — called synchronously right after HWND creation
        # (the original v1.11.0 approach that worked on first launch)
        self._reapply_dwm_shadow_disable()
        
        central_widget = QWidget()
        central_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(CENTRAL_WIDGET_SPACING)
        
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
        self._overflow_menu.addSeparator()
        act_support = self._overflow_menu.addAction("Support Nudge")
        act_support.triggered.connect(self._open_support_dialog)
        act_whatsnew = self._overflow_menu.addAction("What\u2019s New")
        act_whatsnew.triggered.connect(self._show_whats_new)

        # Title bar order: Nudge — Settings — ··· — minimize — close
        # Search lives inline on the Add-tasks field (not in the title bar).
        self.btn_settings = QPushButton()
        self.btn_settings.setObjectName("chromeButton")
        self.btn_settings.setIcon(QIcon(svg_to_pixmap(generate_svg_icon("settings", chrome_color, SETTINGS_ICON_SIZE), SETTINGS_ICON_SIZE)))
        self.btn_settings.setIconSize(QSize(16, 16))
        self.btn_settings.setFixedSize(chrome_btn_sz, chrome_btn_sz)
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.clicked.connect(self.open_settings)
        top_bar.addWidget(self.btn_settings)

        self.btn_menu = QPushButton("\u00b7\u00b7\u00b7")
        self.btn_menu.setObjectName("chromeButton")
        self.btn_menu.setFixedSize(chrome_btn_sz, chrome_btn_sz)
        self.btn_menu.setToolTip("More")
        self.btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_menu.clicked.connect(self._show_overflow_menu)
        top_bar.addWidget(self.btn_menu)

        self.btn_search = None  # search is inline on the add-task field

        self.btn_minimize = QPushButton("-")
        self.btn_minimize.setObjectName("chromeButton")
        self.btn_minimize.setFixedSize(chrome_btn_sz, chrome_btn_sz)
        self.btn_minimize.setToolTip("Minimize")
        self.btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_minimize.clicked.connect(self.showMinimized)
        top_bar.addWidget(self.btn_minimize)

        self.btn_exit = QPushButton("\u2715")
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
        self._group_folder_icon = QLabel()
        self._group_folder_icon.setFixedSize(18, 18)
        self._group_folder_icon.setPixmap(
            svg_to_pixmap(generate_svg_icon("folder", chrome_color, 16), 16)
        )
        self._group_folder_icon.setToolTip("Task group")
        group_row.addWidget(self._group_folder_icon)
        self._group_row_widgets.append(self._group_folder_icon)

        self.group_combo = QComboBox(self)
        self.group_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        group_row.addWidget(self.group_combo, 1)
        self._group_row_widgets.append(self.group_combo)

        self.btn_add_group = QPushButton("+")
        self.btn_add_group.setObjectName("accentIconButton")
        self.btn_add_group.setFixedSize(*ADD_GROUP_BTN_SIZE)
        self.btn_add_group.setToolTip("Add task group")
        self.btn_add_group.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_group.clicked.connect(self._add_group_dialog)
        group_row.addWidget(self.btn_add_group)
        self._group_row_widgets.append(self.btn_add_group)

        self.btn_collapse_groups = QPushButton()
        self.btn_collapse_groups.setObjectName("chromeButton")
        self.btn_collapse_groups.setFixedSize(28, 28)
        self.btn_collapse_groups.setToolTip("Collapse all groups")
        self.btn_collapse_groups.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_collapse_groups.setIcon(
            QIcon(svg_to_pixmap(generate_svg_icon("chevron_right", chrome_color, 14), 14))
        )
        self.btn_collapse_groups.clicked.connect(self._collapse_all_groups)
        group_row.addWidget(self.btn_collapse_groups)
        self._group_row_widgets.append(self.btn_collapse_groups)

        self.btn_expand_focused = QPushButton()
        self.btn_expand_focused.setObjectName("chromeButton")
        self.btn_expand_focused.setFixedSize(28, 28)
        self.btn_expand_focused.setToolTip("Expand focused group only")
        self.btn_expand_focused.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_expand_focused.setIcon(
            QIcon(svg_to_pixmap(generate_svg_icon("chevron_down", chrome_color, 14), 14))
        )
        self.btn_expand_focused.clicked.connect(self._expand_focused_group)
        group_row.addWidget(self.btn_expand_focused)
        self._group_row_widgets.append(self.btn_expand_focused)

        layout.addLayout(group_row)

        self.input_bar = QLineEdit(self)
        self.input_bar.setPlaceholderText(" + Add tasks (split by period)...")
        self.input_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.input_bar.returnPressed.connect(self.process_input)
        self.input_bar.setDragEnabled(True)
        self._search_action = QAction(self.input_bar)
        self._search_action.setToolTip("Search (Ctrl+F)")
        self._search_action.setIcon(QIcon(search_icon_pixmap(theme, 16)))
        self._search_action.triggered.connect(self._toggle_search)
        self.input_bar.addAction(self._search_action, QLineEdit.ActionPosition.TrailingPosition)
        layout.addWidget(self.input_bar)

        self.input_bar.installEventFilter(self)
        self._refresh_group_combo()
        self.group_combo.currentIndexChanged.connect(self._on_group_combo_changed)

        # --- Tag Filter ---
        self._tag_filter = TagFilterDropdown(self)
        self._tag_filter.tags_selected.connect(self._on_tag_filter_changed)
        self._active_tag_filter: list[str] = []
        layout.addWidget(self._tag_filter)

        # --- Task search bar (hidden by default) ---
        self._search_bar = TaskSearchBar(self)
        self._search_bar.search_changed.connect(self._on_search_changed)
        self._search_bar.filters_changed.connect(self._on_search_filters_changed)
        self._search_bar.close_requested.connect(self._close_search)
        self._active_search_text = ""
        self._active_search_scopes = {"tasks", "groups", "tags"}
        layout.addWidget(self._search_bar)

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
        self.tasks_widget.setAcceptDrops(True)
        self._search_bar.set_safe_parent(self.tasks_widget)
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tasks_layout.setSpacing(TASKS_LAYOUT_SPACING)

        self._flat_drop_indicator = QFrame(self.tasks_widget)
        self._flat_drop_indicator.setObjectName("dropIndicator")
        self._flat_drop_indicator.setFixedHeight(DROP_INDICATOR_HEIGHT)
        self._flat_drop_indicator.hide()

        self._group_drop_indicator = QFrame(self.tasks_widget)
        self._group_drop_indicator.setObjectName("dropIndicator")
        self._group_drop_indicator.setFixedHeight(DROP_INDICATOR_HEIGHT)
        self._group_drop_indicator.hide()

        self.scroll_area.setWidget(self.tasks_widget)
        layout.addWidget(self.scroll_area, stretch=1)

        # Sticky group header clone (pinned while scrolling dense lists)
        self._sticky_group_header = QPushButton(self.scroll_area.viewport())
        self._sticky_group_header.setObjectName("groupHeader")
        self._sticky_group_header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sticky_group_header.hide()
        self._sticky_group_header.clicked.connect(self._on_sticky_header_clicked)
        self._sticky_section_id = None
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._update_sticky_group_header)

        self._glow_overlay = GlowOverlay(self.scroll_area.viewport())
        self._glow_overlay.setGeometry(self.scroll_area.viewport().rect())
        self.scroll_area.viewport().installEventFilter(self)

        self._drop_overlay = DropIndicatorOverlay(self.scroll_area.viewport())
        self._drop_overlay.setGeometry(self.scroll_area.viewport().rect())

        # Empty state widget (shown when no tasks)
        self._empty_state_widget = QWidget()
        empty_layout = QVBoxLayout(self._empty_state_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(EMPTY_STATE_SPACING)

        self._empty_state_label = QLabel("Add a task to get started")
        self._empty_state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state_label.setStyleSheet(f"opacity: {OPACITY_FULL}; font-size: {FONT_SIZE_TITLE_MD}px;")
        empty_layout.addWidget(self._empty_state_label)

        self._empty_state_arrow = QLabel("\u2193")
        self._empty_state_arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state_arrow.setStyleSheet(f"font-size: {FONT_SIZE_EMPTY_STATE_ARROW}px; opacity: {OPACITY_ICONS};")
        empty_layout.addWidget(self._empty_state_arrow)

        self._empty_state_timer = QTimer(self)
        self._empty_state_timer.timeout.connect(self._animate_empty_arrow)
        self._empty_state_arrow_visible = True

        layout.addWidget(self._empty_state_widget)
        self._empty_state_widget.hide()

        # --- Search shortcut ---
        self._search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self._search_shortcut.activated.connect(self._toggle_search)

        # --- Separator ---
        self._footer_separator = QFrame()
        self._footer_separator.setFrameShape(QFrame.Shape.HLine)
        self._footer_separator.setFixedHeight(1)
        self._footer_separator.setStyleSheet(f"background: {theme['colors'].get('border', 'rgba(255,255,255,60)')}; border: none;")
        layout.addWidget(self._footer_separator)

        # --- Footer Bar (task count + History shortcut) ---
        self._footer_bar = QWidget()
        self._footer_bar.setStyleSheet("background: transparent; border: none; border-radius: 0px;")
        footer_layout = QHBoxLayout(self._footer_bar)
        footer_layout.setContentsMargins(*FOOTER_MARGINS)
        footer_layout.setSpacing(FOOTER_SPACING)

        self._footer_task_count = QLabel("0 tasks")
        self._footer_task_count.setStyleSheet(f"font-size: {FONT_SIZE_LABEL_MD}px; color: {theme['colors'].get('text_muted', 'rgba(255,255,255,180)')}; background: transparent; border: none;")
        footer_layout.addWidget(self._footer_task_count)

        footer_layout.addStretch()

        self._footer_history_btn = QPushButton()
        self._footer_history_btn.setObjectName("ghostButton")
        self._footer_history_btn.setIcon(QIcon(svg_to_pixmap(generate_svg_icon("history", chrome_color, HISTORY_BTN_ICON_SIZE), HISTORY_BTN_ICON_SIZE)))
        self._footer_history_btn.setIconSize(QSize(12, 12))
        self._footer_history_btn.setText("History")
        self._footer_history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._footer_history_btn.clicked.connect(self.open_history)
        self._footer_history_btn.setStyleSheet(footer_history_button_stylesheet(theme))
        footer_layout.addWidget(self._footer_history_btn)

        layout.addWidget(self._footer_bar)

        layout.setContentsMargins(*CENTRAL_WIDGET_MARGINS)

        self.setCentralWidget(central_widget)
        self._dim_overlay = DimOverlay(central_widget)
        self._dim_overlay.apply_theme(theme)
        self._enable_resize_hover_tracking(central_widget)
        # Let the glass panel and task list grow when the user resizes the window.
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _animate_empty_arrow(self):
        self._empty_state_arrow_visible = not self._empty_state_arrow_visible
        self._empty_state_arrow.setStyleSheet(
            f"font-size: {FONT_SIZE_EMPTY_STATE_ARROW}px; opacity: {OPACITY_ICONS if self._empty_state_arrow_visible else OPACITY_DIM};"
        )

    def _update_empty_state(self):
        has_tasks = len(self.tasks) > 0
        self._empty_state_widget.setVisible(not has_tasks)
        self.scroll_area.setVisible(has_tasks)
        # Show tag filter only if enabled in settings and there are tasks with tags
        has_tags = any(task.get("tags") for task in self.tasks)
        tag_filter_enabled = self.app_state.get("tagFilterEnabled", False)
        self._tag_filter.setVisible(has_tasks and has_tags and tag_filter_enabled)
        # Update footer task count
        total = len(self.tasks)
        if total == 0:
            self._footer_task_count.setText("0 tasks")
        elif total == 1:
            self._footer_task_count.setText("1 task")
        else:
            self._footer_task_count.setText(f"{total} tasks")
        if not has_tasks:
            self._empty_state_timer.start(EMPTY_STATE_BLINK_MS)
        else:
            self._empty_state_timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_glow_overlay') and self.scroll_area is not None:
            self._glow_overlay.setGeometry(self.scroll_area.viewport().rect())
        if hasattr(self, '_drop_overlay') and self.scroll_area is not None:
            self._drop_overlay.setGeometry(self.scroll_area.viewport().rect())
        if not self._resize_live:
            self._begin_live_resize()
        if self._resize_timer.isActive():
            self._resize_timer.stop()
        self._resize_timer.start(RESIZE_DEBOUNCE_MS)

    def _begin_live_resize(self) -> None:
        """Pause expensive task-list work while the user drags a resize edge."""
        self._resize_live = True
        if self.tasks_widget is not None:
            self.tasks_widget.setUpdatesEnabled(False)

    def _on_resize_settled(self) -> None:
        """Re-enable painting and sync wrapping layouts once geometry is stable."""
        self._resize_timer.stop()
        if self.tasks_widget is not None:
            self.tasks_widget.setUpdatesEnabled(True)
        was_live = self._resize_live
        self._resize_live = False
        self._sync_task_row_text_layouts()
        if was_live and self.tasks_widget is not None:
            self.tasks_widget.update()

    def _sync_hotkey_hwnd(self):
        """Re-bind RegisterHotKey to the current native window handle.

        ``setWindowFlags`` destroys/recreates the HWND; hotkeys registered
        against the old handle stop working until moved.
        """
        try:
            self._hotkey_filter.set_hwnd(int(self.winId()))
        except Exception:
            logging.exception("Failed to sync hotkey HWND")

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_hotkey_hwnd()
        if not self._hotkey_registered_on_show:
            self._hotkey_registered_on_show = True
            self._shortcut_manager.update_shortcuts()
            self._sync_hotkey_hwnd()
        QTimer.singleShot(DEFERRED_RENDER_MS, self._reapply_dwm_shadow_disable)
        self._sync_task_list_viewport_width()
        self._sync_task_row_text_layouts()

    def _fix_line_edit_cursors(self, app) -> None:
        """Set palette on all QLineEdits so cursor is visible (QSS caret-color is not supported)."""
        from PyQt6.QtGui import QColor, QPalette
        theme = get_theme(normalize_theme_id(self.app_state.get("theme", "dark")))
        text_color = theme["colors"]["text"]
        accent_color = theme["colors"]["accent"]
        for le in app.findChildren(QLineEdit):
            p = le.palette()
            p.setColor(QPalette.ColorRole.Text, QColor(text_color))
            p.setColor(QPalette.ColorRole.Highlight, QColor(accent_color))
            p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            le.setPalette(p)

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
        host = self.tasks_widget
        if host is not None:
            host.setUpdatesEnabled(False)
        try:
            if self.tasks_layout is not None:
                self.tasks_layout.activate()
            for section in self.group_sections.values():
                if hasattr(section, "force_layout"):
                    section.force_layout()
            for row in self.task_row_widgets.values():
                if hasattr(row, "sync_text_layout"):
                    row.sync_text_layout()
        finally:
            if host is not None:
                host.setUpdatesEnabled(True)

    def init_keyboard_shortcuts(self):
        self._shortcut_manager.register_all()

    def update_keyboard_shortcuts(self):
        self._shortcut_manager.update_shortcuts()

    def process_input(self):
        self._task_controller.process_input()

    def _current_input_group_id(self) -> str:
        group_id = self.group_combo.currentData()
        return group_id if group_id else GENERAL_GROUP_ID

    def _on_escape_pressed(self):
        if self.input_bar.hasFocus():
            self.input_bar.clear()
            return
        self._escape_count += 1
        if self._escape_count >= ESCAPE_PRESS_THRESHOLD:
            self._escape_count = 0
            self._escape_timer.stop()
            self._force_quit = True
            self.close()
        else:
            self._escape_timer.start(500)

    def eventFilter(self, obj, event):
        if not hasattr(self, 'scroll_area'):
            return super().eventFilter(obj, event)
        if (
            self._frameless_chrome is not None
            and event.type() == QEvent.Type.MouseMove
            and not self._frameless_chrome.is_resizing
            and not self._frameless_chrome.is_dragging
        ):
            global_pos = event.globalPosition().toPoint()
            local_pos = self.mapFromGlobal(global_pos)
            self._frameless_chrome.update_hover_cursor(local_pos)
        if obj is self.scroll_area.viewport():
            if event.type() == QEvent.Type.MouseMove:
                if self.app_state.get("mouseGlow", True):
                    self._glow_overlay.setGeometry(self.scroll_area.viewport().rect())
                    self._glow_overlay.set_glow_center(event.position())
                if hasattr(self, '_drop_overlay'):
                    self._drop_overlay.setGeometry(self.scroll_area.viewport().rect())
                return False
            elif event.type() == QEvent.Type.Enter:
                if self.app_state.get("mouseGlow", True):
                    self._glow_overlay.setGeometry(self.scroll_area.viewport().rect())
                if hasattr(self, '_drop_overlay'):
                    self._drop_overlay.setGeometry(self.scroll_area.viewport().rect())
                return False
            elif event.type() == QEvent.Type.Leave:
                self._glow_overlay.hide_glow()
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
            elif event.mimeData().hasText() or event.mimeData().hasUrls():
                theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
                self._drop_overlay.show_overlay(theme_id)
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
            elif event.mimeData().hasText() or event.mimeData().hasUrls():
                event.acceptProposedAction()
                return True
        elif event.type() == QEvent.Type.DragLeave and obj is self.tasks_widget:
            self._flat_drop_indicator.hide()
            self._group_drop_indicator.hide()
            self._drop_overlay.hide_overlay()
            event.accept()
            return True
        elif event.type() == QEvent.Type.Drop and obj is self.tasks_widget:
            self._flat_drop_indicator.hide()
            self._group_drop_indicator.hide()
            self._drop_overlay.hide_overlay()
            source = event.source()
            if source is not None and hasattr(source, "_task_ref"):
                self._on_flat_list_drop(source, event.position().toPoint())
                event.acceptProposedAction()
                return True
            elif event.mimeData().hasFormat("application/x-nudge-group"):
                self._on_group_drop(event.position().toPoint(), event.mimeData())
                event.acceptProposedAction()
                return True
            elif event.mimeData().hasText() or event.mimeData().hasUrls():
                self._on_external_drop(event.mimeData())
                event.acceptProposedAction()
                return True
        return super().eventFilter(obj, event)

    def _on_external_drop(self, mime_data) -> None:
        """Handle external drag-and-drop (text, URLs, files)."""
        import logging
        logger = logging.getLogger(__name__)
        items = []
        if mime_data.hasUrls():
            for url in mime_data.urls():
                local_path = url.toLocalFile()
                if local_path:
                    items.append({"type": "file", "content": local_path})
                else:
                    items.append({"type": "text", "content": url.toString()})
        elif mime_data.hasHtml():
            items.append({"type": "html", "content": mime_data.html()})
        elif mime_data.hasText():
            items.append({"type": "text", "content": mime_data.text()})

        if not items:
            return

        logger.info("External drop: %d items", len(items))
        for item in items:
            logger.info("  - [%s] %s", item["type"], item["content"][:80])

        if hasattr(self, '_task_controller'):
            self._task_controller.create_tasks_from_drop(items)

    def _on_clipboard_import(self) -> None:
        """Handle Ctrl+Shift+V — import tasks from clipboard text."""
        if not hasattr(self, '_task_controller'):
            return
        count = self._task_controller.import_from_clipboard()
        if count > 0:
            from src.frontend.info_toast import InfoToast
            word = "task" if count == 1 else "tasks"
            toast = InfoToast(self, f"Imported {count} {word}")
            toast.show()

    def _refresh_group_combo(self, select_group_id: str | None = None) -> None:
        if not hasattr(self, '_group_controller'):
            return
        self._group_controller._refresh_group_combo(select_group_id)

    def _save_group_expanded(self, group_id: str, expanded: bool) -> None:
        self._group_controller._save_group_expanded(group_id, expanded)

    def _select_active_group(self, group_id: str) -> None:
        self._group_controller._select_active_group(group_id)

    def _on_group_combo_changed(self, index: int) -> None:
        self.render_tasks()

    def _add_group_dialog(self) -> None:
        self._group_controller._add_group_dialog()

    def _collapse_all_groups(self) -> None:
        for section in self.group_sections.values():
            section.set_content_expanded(False, persist=True)
        self._update_sticky_group_header()

    def _expand_focused_group(self) -> None:
        """Collapse all groups except the one selected in the combo (or first)."""
        focus_id = None
        if hasattr(self, "group_combo") and self.group_combo.count():
            focus_id = self.group_combo.currentData()
        if not focus_id and self.group_sections:
            focus_id = next(iter(self.group_sections))
        for gid, section in self.group_sections.items():
            section.set_content_expanded(gid == focus_id, persist=True)
        self._update_sticky_group_header()

    def _on_sticky_header_clicked(self) -> None:
        gid = self._sticky_section_id
        if gid and gid in self.group_sections:
            section = self.group_sections[gid]
            section.set_content_expanded(not section._expanded, persist=True)
            self._update_sticky_group_header()

    def _update_sticky_group_header(self, *_args) -> None:
        if not hasattr(self, "_sticky_group_header"):
            return
        groups_enabled = self.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)
        if not groups_enabled or not self.group_sections:
            self._sticky_group_header.hide()
            self._sticky_section_id = None
            return
        vp = self.scroll_area.viewport()
        sticky = None
        for section in self.group_sections.values():
            if section.isHidden():
                continue
            top_left = section.mapTo(vp, QPoint(0, 0))
            # Section scrolled up but still intersecting viewport
            if top_left.y() < 0 and top_left.y() + section.height() > 28:
                sticky = section
                break
        if sticky is None:
            self._sticky_group_header.hide()
            self._sticky_section_id = None
            return
        self._sticky_section_id = sticky.group_id
        self._sticky_group_header.setText(sticky.header_btn.text())
        self._sticky_group_header.setIcon(sticky.header_btn.icon())
        self._sticky_group_header.setIconSize(sticky.header_btn.iconSize())
        w = vp.width()
        h = max(32, sticky.header_btn.sizeHint().height())
        self._sticky_group_header.setGeometry(0, 0, w, h)
        self._sticky_group_header.raise_()
        self._sticky_group_header.show()

    def _rename_group(self, group_id: str) -> None:
        self._group_controller._rename_group(group_id)

    def _delete_group(self, group_id: str) -> None:
        self._group_controller._delete_group(group_id)

    def _move_group_order(self, group_id: str, offset: int) -> None:
        self._group_controller._move_group_order(group_id, offset)

    def _show_group_header_menu(self, group_id: str, global_pos) -> None:
        self._group_controller._show_group_header_menu(group_id, global_pos)

    def _move_task_to_group(self, task_ref: dict, target_group_id: str) -> None:
        self._group_controller._move_task_to_group(task_ref, target_group_id)

    def _tasks_in_group(self, group_id: str) -> list:
        return self._group_controller._tasks_in_group(group_id)
        
    def render_tasks(self):
        if not hasattr(self, '_task_controller'):
            return
        groups_enabled = self.app_state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED)
        for w in self._group_row_widgets:
            w.setVisible(groups_enabled)
        self._task_controller.render_tasks()
        QTimer.singleShot(0, self._update_sticky_group_header)

    def _on_tag_filter_changed(self, tags: list[str]):
        """Handle tag filter selection change."""
        self._active_tag_filter = tags
        self._apply_task_visibility_filters()

    def _task_matches_tag_filter(self, task: dict) -> bool:
        """Check if a task matches the current tag filter."""
        if not self._active_tag_filter:
            return True
        task_tags = task.get("tags", [])
        return any(tag in task_tags for tag in self._active_tag_filter)

    def _task_text_matches_search(self, task: dict) -> bool:
        query = (self._active_search_text or "").strip().lower()
        if not query:
            return False
        return query in task.get("text", "").lower()

    def _task_tag_matches_search(self, task: dict) -> bool:
        query = (self._active_search_text or "").strip().lower()
        if not query:
            return False
        return any(query in tag.lower() for tag in task.get("tags", []))

    def _task_matches_search(self, task: dict) -> bool:
        """Task matches if text/tags hit and the matching scope chip is active."""
        query = (self._active_search_text or "").strip().lower()
        if not query:
            return True
        scopes = getattr(self, "_active_search_scopes", {"tasks", "groups", "tags"})
        text_hit = self._task_text_matches_search(task)
        tag_hit = self._task_tag_matches_search(task)
        if text_hit and "tasks" in scopes:
            return True
        if tag_hit and "tags" in scopes:
            return True
        return False

    def _group_matches_search(self, group: dict) -> bool:
        query = (self._active_search_text or "").strip().lower()
        if not query:
            return False
        if "groups" not in getattr(self, "_active_search_scopes", {"groups"}):
            return False
        return query in group.get("name", "").lower()

    def _task_is_visible(self, task: dict) -> bool:
        return self._task_matches_tag_filter(task) and self._task_matches_search(task)

    def _apply_tag_filter(self):
        """Show/hide task rows based on active tag + search filters."""
        self._apply_task_visibility_filters()

    def _apply_task_visibility_filters(self):
        """Apply tag filter and search together with scope chips + type labels."""
        searching = bool((self._active_search_text or "").strip())
        query = (self._active_search_text or "").strip()
        has_results = False

        for _key, row in self.task_row_widgets.items():
            task = getattr(row, "_task_ref", None)
            if task is None:
                row.setVisible(False)
                continue
            visible = self._task_is_visible(task)
            row.setVisible(visible)
            if visible and searching:
                has_results = True
                kind = "tag" if (
                    self._task_tag_matches_search(task)
                    and not self._task_text_matches_search(task)
                ) else "task"
                if hasattr(row, "apply_search_highlight"):
                    row.apply_search_highlight(query, match_kind=kind)
            elif hasattr(row, "apply_search_highlight"):
                row.apply_search_highlight("")

        for group_id, section in self.group_sections.items():
            group_hit = searching and self._group_matches_search(section.group)
            visible_count = 0
            for row in section.task_rows:
                task = getattr(row, "_task_ref", None)
                if task is not None and self._task_is_visible(task):
                    visible_count += 1

            if visible_count == 0 and not group_hit:
                section.setVisible(False)
                if hasattr(section, "set_search_type_label"):
                    section.set_search_type_label(False)
                continue

            section.setVisible(True)
            has_results = True
            if hasattr(section, "set_search_type_label"):
                section.set_search_type_label(group_hit)
            if searching:
                section.set_content_expanded(True, persist=False)
            else:
                section.set_content_expanded(
                    bool(section.group.get("expanded", True)),
                    persist=False,
                )
            section.refresh_header_count(
                visible_count if searching or self._active_tag_filter else None
            )

        if hasattr(self, "_search_bar"):
            self._search_bar.set_has_results(has_results if searching else False)

    # --- Search bar methods ---

    def _toggle_search(self):
        # Clicking the search action while open should close. Suppress the
        # FocusOut→close race that would hide the bar then immediately reopen it.
        if self._search_bar.isVisible():
            self._search_bar.suppress_next_focus_close()
            self._close_search()
            return
        # If FocusOut already closed us within this click, don't reopen.
        closed_at = getattr(self, "_search_closed_at", 0.0)
        if closed_at and (time.monotonic() - closed_at) < 0.3:
            return
        self._open_search()

    def _open_search(self):
        self._search_closed_at = 0.0
        self._active_search_scopes = {"tasks", "groups", "tags"}
        self._search_bar.activate()

    def _close_search(self):
        self._search_closed_at = time.monotonic()
        self._search_bar.deactivate()

    def _on_search_changed(self, text: str):
        self._active_search_text = text
        self._apply_task_visibility_filters()

    def _on_search_filters_changed(self, scopes: set):
        self._active_search_scopes = set(scopes) if scopes else {"tasks", "groups", "tags"}
        self._apply_task_visibility_filters()

    def _apply_search_filter(self):
        self._apply_task_visibility_filters()

    def _update_tag_filter(self):
        """Update the tag filter dropdown with current tags."""
        self._tag_filter.update_tags(self.tasks)

    def _append_task_row_widget(self, task: dict) -> TaskRowWidget:
        return self._task_controller._append_task_row_widget(task)

    def _remove_task_row_widget(self, task: dict) -> None:
        self._task_controller._remove_task_row_widget(task)

    def _bold_font(self):
        """Return a bold font for menu indicators."""
        from PyQt6.QtGui import QFont
        font = QFont()
        font.setBold(True)
        return font

    def _style_context_menu(self, menu: QMenu) -> None:
        theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        menu.setStyleSheet(menu_stylesheet(theme))

    def show_task_context_menu(self, task_ref):
        self._menu_builder.show_task_context_menu(task_ref)

    def edit_task(self, task_ref):
        self._task_controller.edit_task(task_ref)

    def update_task_text(self, task_ref, new_text):
        self._task_controller.update_task_text(task_ref, new_text)

    def _reorder_task(self, task_ref, new_idx):
        self._task_controller._reorder_task(task_ref, new_idx)

    def move_task(self, task_ref, offset):
        self._task_controller.move_task(task_ref, offset)

    def move_task_to_top(self, task_ref):
        self._task_controller.move_task_to_top(task_ref)

    def move_task_to_bottom(self, task_ref):
        self._task_controller.move_task_to_bottom(task_ref)

    def _on_flat_list_drop(self, row_widget, pos: QPoint) -> None:
        self._task_controller._on_flat_list_drop(row_widget, pos)

    def _layout_stretch_index(self) -> int:
        return self._task_controller._layout_stretch_index()

    def _update_flat_drop_indicator(self, pos: QPoint) -> None:
        self._task_controller._update_flat_drop_indicator(pos)

    def _update_group_drop_indicator(self, pos: QPoint) -> None:
        self._task_controller._update_group_drop_indicator(pos)

    def _on_group_drop(self, pos: QPoint, mime_data) -> None:
        self._task_controller._on_group_drop(pos, mime_data)

    def _on_row_dropped(self, row_widget, target_group_id, insert_index):
        self._task_controller._on_row_dropped(row_widget, target_group_id, insert_index)

    def delete_task(self, task_ref):
        self._task_controller.delete_task(task_ref)

    def toggle_task(self, task_ref, is_checked):
        self._task_controller.toggle_task(task_ref, is_checked)

    def archive_task(self, task_ref):
        self._task_controller.archive_task(task_ref)

    def _show_undo_toast(self, task_text):
        self._task_controller._show_undo_toast(task_text)

    def _undo_last_archive(self):
        self._task_controller._undo_last_archive()

    def migrate_completed_tasks_to_history(self):
        self._task_controller.migrate_completed_tasks_to_history()

    def restore_task_from_history(self, task_ref):
        self._task_controller.restore_task_from_history(task_ref)

    def contextMenuEvent(self, event):
        self._menu_builder.contextMenuEvent(event)

    def clear_completed_tasks(self):
        self._task_controller.clear_completed_tasks()

    def _place_dialog_near_geometry(
        self,
        dialog: QDialog,
        ref_geom,
        *,
        y_offset: int = 0,
        prefer_right: bool = False,
    ) -> None:
        """Place a dialog beside a reference rect, clamped to the screen work area (H6)."""
        self._dialog_manager.place_dialog_near_geometry(dialog, ref_geom, y_offset=y_offset, prefer_right=prefer_right)

    def _place_dialog_near_main_window(self, dialog: QDialog, *, y_offset: int = 0) -> None:
        """Place a dialog beside the main window, clamped to the screen work area (H6)."""
        self._dialog_manager.place_dialog_near_main_window(dialog, y_offset=y_offset)

    def _window_rects_to_avoid(self, extra: QDialog | None = None) -> list:
        """Rects export must not overlap: main window plus any open side panel."""
        return self._dialog_manager.window_rects_to_avoid(extra)

    def _place_dialog_avoiding_rects(
        self,
        dialog: QDialog,
        avoid_rects: list,
        *,
        y_offset: int = 0,
        gap: int = 15,
    ) -> None:
        """Place dialog beside app windows without overlapping them (H6b)."""
        self._dialog_manager.place_dialog_avoiding_rects(dialog, avoid_rects, y_offset=y_offset, gap=gap)

    def _run_side_dialog(self, dialog: QDialog) -> None:
        """Show a non-modal side panel and track it for export avoidance."""
        self._dialog_manager.run_side_dialog(dialog)

    def _on_side_dialog_closed(self, dialog: QDialog) -> None:
        is_history = dialog is self._dialog_manager._history_dialog
        self._dialog_manager._on_side_dialog_closed(dialog)
        if is_history:
            self._task_ctx.history_dialog = None

    def open_history(self):
        # FIX-D1: suppress shortcut only when our own input bar has focus
        focused = QApplication.focusWidget()
        if focused is getattr(self, 'input_bar', None):
            return
        if self._dialog_manager._history_dialog is not None:
            self._dialog_manager._history_dialog.close()
            return
        dialog = HistoryDialog(
            self.history_store,
            self.restore_task_from_history,
            self.groups_data,
            self,
            self.state_manager,
        )
        self._dialog_manager._history_dialog = dialog
        self._task_ctx.history_dialog = dialog
        self.theme_applied.connect(dialog._on_parent_theme_applied)
        self._dialog_manager.center_on_parent(dialog)
        self._run_side_dialog(dialog)

    def open_reminders(self) -> None:
        from src.frontend.dialog_context import DialogContext
        from src.frontend.reminders_list_dialog import RemindersListDialog

        # FIX-D1: suppress shortcut only when our own input bar has focus
        focused = QApplication.focusWidget()
        if focused is getattr(self, 'input_bar', None):
            return
        if self._dialog_manager._reminders_dialog is not None:
            self._dialog_manager._reminders_dialog.close()
            return
        ctx = DialogContext(
            app_state=self.app_state,
            state_manager=self.state_manager,
            timer_manager=self._timer_manager,
            screen=lambda: self.screen(),
            frame_geometry=self.frameGeometry,
            window_rects_to_avoid=self._dialog_manager.window_rects_to_avoid,
            place_dialog_avoiding_rects=self._dialog_manager.place_dialog_avoiding_rects,
        )
        dialog = RemindersListDialog(ctx, parent=self)
        self._dialog_manager._reminders_dialog = dialog
        avoid = self._window_rects_to_avoid()
        self._place_dialog_avoiding_rects(dialog, avoid)
        self._run_side_dialog(dialog)

    def open_settings(self):
        # FIX-D1: suppress shortcut only when our own input bar has focus
        focused = QApplication.focusWidget()
        if focused is getattr(self, 'input_bar', None):
            return
        if self._dialog_manager._settings_dialog is not None:
            self._dialog_manager._settings_dialog.close()
            return
        dialog = SettingsDialog(self.state_manager, self)
        self._dialog_manager._settings_dialog = dialog
        self.theme_applied.connect(dialog._on_parent_theme_applied)
        self._dialog_manager.center_on_parent(dialog)
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

    def _purge_old_history(self) -> None:
        """Remove history tasks older than the configured retention period."""
        retention_days = self.app_state.get("historyRetentionDays", DEFAULT_HISTORY_RETENTION_DAYS)
        if retention_days == 0:
            return  # 0 = Forever
        history = self.history_store.load()
        if not history:
            return
        cutoff = datetime.now().timestamp() - (retention_days * SECONDS_PER_DAY)
        kept = []
        for task in history:
            completed_at = task.get("completedAt", "")
            if not completed_at:
                kept.append(task)
                continue
            try:
                ts = datetime.fromisoformat(completed_at).timestamp()
                if ts >= cutoff:
                    kept.append(task)
            except (ValueError, TypeError):
                kept.append(task)
        if len(kept) != len(history):
            self.history_store.save(kept)

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
        self._task_controller._set_task_reminder(task_ref, minutes_from_now, repeat)

    def _set_task_reminder_at_time(self, task_ref, time_str: str, days_ahead: int = 0):
        self._task_controller._set_task_reminder_at_time(task_ref, time_str, days_ahead)

    def _clear_task_reminder(self, task_ref):
        self._task_controller._clear_task_reminder(task_ref)

    def _set_task_due_date(self, task_ref, date_str):
        self._task_controller._set_task_due_date(task_ref, date_str)

    def _clear_task_due_date(self, task_ref):
        self._task_controller._clear_task_due_date(task_ref)

    def _show_custom_due_date_dialog(self, task_ref: dict) -> None:
        self._task_controller._show_custom_due_date_dialog(task_ref)

    def _set_task_priority(self, task_ref, priority):
        self._task_controller._set_task_priority(task_ref, priority)

    def _clear_task_priority(self, task_ref):
        self._task_controller._clear_task_priority(task_ref)

    def _set_task_recurrence(self, task_ref, recurrence_type, interval):
        self._task_controller._set_task_recurrence(task_ref, recurrence_type, interval)

    def _clear_task_recurrence(self, task_ref):
        self._task_controller._clear_task_recurrence(task_ref)

    def _show_custom_recurrence_dialog(self, task_ref: dict) -> None:
        self._task_controller._show_custom_recurrence_dialog(task_ref)

    def _show_custom_reminder_dialog(self, task_ref: dict) -> None:
        self._task_controller._show_custom_reminder_dialog(task_ref)

    def _show_overflow_menu(self):
        self._style_overflow_menu()
        btn_pos = self.btn_menu.mapToGlobal(QPoint(0, self.btn_menu.height()))
        menu_width = self._overflow_menu.sizeHint().width()
        self._overflow_menu.exec(QPoint(btn_pos.x() - menu_width + self.btn_menu.width(), btn_pos.y()))

    def _style_overflow_menu(self):
        theme_id = normalize_theme_id(self.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        self._overflow_menu.setStyleSheet(overflow_menu_stylesheet(theme))

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
                f"Version: {__version__}",
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
        if self._dialog_manager._export_dialog is not None:
            self._dialog_manager._export_dialog.close()
            return

        from src.frontend.export_dialog import ExportDialog

        dialog = ExportDialog(self, self)
        self._dialog_manager._export_dialog = dialog
        avoid = self._window_rects_to_avoid(anchor)
        self._place_dialog_avoiding_rects(dialog, avoid)
        dialog.finished.connect(lambda r, d=dialog: self._on_side_dialog_closed(d))
        dialog.show()



