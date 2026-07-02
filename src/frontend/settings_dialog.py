"""Settings dialog with tabs for General, Shortcuts, and About."""

from datetime import datetime

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QColor, QKeySequence
from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
                             QGraphicsDropShadowEffect, QHBoxLayout,
                             QKeySequenceEdit, QLabel, QListWidget,
                             QListWidgetItem, QPushButton, QScrollArea,
                             QSizePolicy, QSlider, QStackedWidget, QVBoxLayout,
                             QWidget)

from src.backend.defaults import (DEFAULT_ALWAYS_ON_TOP,
                                   DEFAULT_ALWAYS_ON_TOP_SHORTCUT,
                                   DEFAULT_CHECK_FOR_UPDATES,
                                   DEFAULT_EXPORT_SHORTCUT,
                                   DEFAULT_GROUPS_ENABLED,
                                   DEFAULT_HISTORY_RETENTION_DAYS,
                                   DEFAULT_HISTORY_SHORTCUT, DEFAULT_MOUSE_GLOW,
                                   DEFAULT_PIN_SHORTCUT,
                                   DEFAULT_PINNED_TO_DESKTOP,
                                   DEFAULT_PLAY_COMPLETION_SOUND,
                                   DEFAULT_POSITION_LOCKED,
                                   DEFAULT_REMINDERS_SHORTCUT,
                                   DEFAULT_SETTINGS_SHORTCUT,
                                   DEFAULT_SHOW_BOOT_NOTIFICATION,
                                   DEFAULT_START_ON_BOOT,
                                   DEFAULT_TAG_FILTER_ENABLED,
                                   DEFAULT_TASK_FONT, DEFAULT_TASK_TEXT_SIZE,
                                   DEFAULT_THEME)
from src.backend.icon import get_app_icon
from src.backend.task_groups import sorted_groups
from src.backend.window_layer import reconcile_layer_settings
from src.constants import (BTN_HEIGHT_LG, BTN_HEIGHT_MD,
                           EXPORT_COMBO_HEIGHT, FONT_SIZE_LABEL_SM,
                           FONT_SIZE_TITLE_MD, KEY_SEQ_EDIT_WIDTH,
                           MARGIN_SETTINGS_TAB, OPACITY_DIVISOR,
                           OPACITY_SLIDER_MAX, OPACITY_SLIDER_MIN,
                           RADIUS_PANEL, SCROLL_AREA_MAX_HEIGHT,
                           SCROLL_AREA_MIN_HEIGHT, SETTINGS_APPEARANCE_TAB_SPACING,
                           SETTINGS_EXPORT_GROUP_CONTENT_MARGINS,
                           SETTINGS_GLOW_BLUR_RADIUS,
                           SETTINGS_MAIN_LAYOUT_MARGINS,
                           SETTINGS_MAX_CLAMP_OFFSET,
                           SETTINGS_SHORTCUT_CARD_MARGINS,
                           SETTINGS_VALUE_LABEL_MIN_WIDTH,
                           SETTINGS_DIALOG_MIN,
                           SPACING_LG, SPACING_MD, SPACING_SM,
                           TEXT_SIZE_SLIDER_MAX)
from src.frontend.frameless_chrome import FramelessChromeController
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.theme import (get_theme, normalize_theme_id,
                                refresh_glass_shells,
                                settings_scroll_area_stylesheet)
from src.frontend.theme_widgets import (SettingsCardWidget, ThemeCardWidget,
                                        ToggleSwitchRow, ToggleSwitchWidget)
from src.frontend.themed_message_dialog import ThemedMessageDialog
from src.frontend.utils import set_label_point_size


class SettingsDialog(GlassPanelDialog):
    def __init__(self, state_manager, parent=None):
        super().__init__(parent, overlap_radius=RADIUS_PANEL, escape_action="close")
        self.state_manager = state_manager
        self.text_size = int(self.state_manager.state.get("taskTextSize", FONT_SIZE_TITLE_MD))
        self._saved_snapshot = {}
        self._initialized = False
        self.history_shortcut_edit = None
        self.settings_shortcut_edit = None
        self.pin_shortcut_edit = None
        self.always_on_top_shortcut_edit = None
        self.toggle_tray_shortcut_edit = None
        self.export_shortcut_edit = None
        self.reminders_shortcut_edit = None
        self._chrome = None
        self.init_ui()

    def _build_snapshot(self):
        return {
            "startOnBoot": self.startup_cb.isChecked(),
            "positionLocked": self.lock_cb.isChecked(),
            "pinnedToDesktop": self.pin_cb.isChecked(),
            "alwaysOnTop": self.always_on_top_cb.isChecked(),
            "theme": self._get_selected_theme(),
            "opacity": self.opacity_slider.value() / OPACITY_DIVISOR,
            "taskTextSize": self.text_size_slider.value(),
            "historyShortcut": self.history_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "settingsShortcut": self.settings_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "pinShortcut": self.pin_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "alwaysOnTopShortcut": self.always_on_top_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "toggleTrayShortcut": self.toggle_tray_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "exportShortcut": self.export_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "remindersShortcut": self.reminders_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
            "groupsEnabled": self.groups_enabled_cb.isChecked(),
            "tagFilterEnabled": self.tag_filter_cb.isChecked(),
            "playCompletionSound": self.completion_sound_cb.isChecked(),
            "historyRetentionDays": [5, 7, 14, 30, 60, 90, 180, 365, 0][self.retention_combo.currentIndex()],
            "checkForUpdates": self.check_updates_cb.isChecked(),
        }

    def _load_sequence(self, value, fallback):
        sequence_text = value or fallback
        return QKeySequence.fromString(sequence_text, QKeySequence.SequenceFormat.PortableText)

    def _mark_dirty(self):
        self._has_unsaved_changes = self._build_snapshot() != self._saved_snapshot
        if hasattr(self, 'save_btn'):
            self.save_btn.setEnabled(self._has_unsaved_changes)

    def _auto_save_appearance(self):
        """Persist appearance settings to disk immediately."""
        self.state_manager.state["theme"] = self._get_selected_theme()
        if hasattr(self, 'text_size_slider'):
            self.state_manager.state["taskTextSize"] = self.text_size_slider.value()
        if hasattr(self, 'opacity_slider'):
            self.state_manager.state["opacity"] = self.opacity_slider.value() / OPACITY_DIVISOR
        if hasattr(self, 'font_combo'):
            self.state_manager.state["taskFont"] = self.font_combo.currentText()
        if hasattr(self, 'mouse_glow_toggle'):
            self.state_manager.state["mouseGlow"] = self.mouse_glow_toggle.isChecked()
        self.state_manager.save()
        if self._initialized:
            self._saved_snapshot = self._build_snapshot()
            self._has_unsaved_changes = False
            if hasattr(self, 'save_btn'):
                self.save_btn.setEnabled(False)

    def _select_theme(self, theme_id):
        for tid, card in self._theme_cards.items():
            card.set_selected(tid == theme_id)
            card.update_theme(theme_id)
        for card in getattr(self, '_settings_cards', []):
            card.update_theme(theme_id)
        self._apply_entry_widget_theming(theme_id)
        parent = self.parent()
        if parent and hasattr(parent, "app_state"):
            parent.app_state["theme"] = theme_id
            parent.apply_app_theme()
        self._auto_save_appearance()

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
            self.reminders_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText),
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
        from src.frontend.themed_message_dialog import ThemedMessageDialog
        if not ThemedMessageDialog.question(
            self,
            "Reset to Defaults",
            "Reset all settings on this tab to defaults?",
        ):
            return

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
        self.text_size_slider.setValue(FONT_SIZE_TITLE_MD)
        self.opacity_slider.setValue(OPACITY_SLIDER_MAX)

    def _reset_shortcuts_tab_defaults(self) -> None:
        defaults = {
            "history_shortcut_edit": "Ctrl+H",
            "settings_shortcut_edit": "Ctrl+,",
            "pin_shortcut_edit": "Ctrl+P",
            "always_on_top_shortcut_edit": "Alt+T",
            "toggle_tray_shortcut_edit": "Ctrl+M",
            "export_shortcut_edit": "Ctrl+E",
            "reminders_shortcut_edit": "Alt+R",
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
        self.completion_sound_cb.setChecked(True)

    def _reset_help_tab_defaults(self):
        pass

    def _create_tab_label(self, text):
        label = QLabel(text)
        set_label_point_size(label, FONT_SIZE_TITLE_MD)
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
        set_label_point_size(label, FONT_SIZE_TITLE_MD)
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
        screen = self.screen() or (QApplication.primaryScreen() if QApplication.instance() else None)
        saved_w, saved_h = self.state_manager.get_settings_window_size()
        if screen:
            available = screen.availableGeometry()
            max_h = available.height() - SETTINGS_MAX_CLAMP_OFFSET
            max_w = available.width() - SETTINGS_MAX_CLAMP_OFFSET
            w = min(saved_w, max_w)
            h = min(saved_h, max_h)
        else:
            w, h = saved_w, saved_h
        self.resize(w, h)
        self.setMinimumSize(*SETTINGS_DIALOG_MIN)
        self.setMouseTracking(True)
        self._chrome = FramelessChromeController(self, min_width=SETTINGS_DIALOG_MIN[0], min_height=SETTINGS_DIALOG_MIN[1])

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*SETTINGS_MAIN_LAYOUT_MARGINS)
        layout.setSpacing(SPACING_MD)

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
        general_layout.setContentsMargins(*MARGIN_SETTINGS_TAB)
        general_layout.setSpacing(SPACING_LG)

        # Startup & System card
        self._settings_cards = []
        startup_card = SettingsCardWidget("Startup & System")
        self._settings_cards.append(startup_card)

        self.startup_cb = self._create_checkbox_row("Run on Startup (Registry)", self.state_manager.state.get("startOnBoot", DEFAULT_START_ON_BOOT))
        startup_card.add_widget(self.startup_cb)

        self.check_updates_cb = self._create_checkbox_row("Check for updates at startup", self.state_manager.state.get("checkForUpdates", DEFAULT_CHECK_FOR_UPDATES))
        startup_card.add_widget(self.check_updates_cb)

        self.boot_notification_cb = self._create_checkbox_row("Show boot notification for pending tasks", self.state_manager.state.get("showBootNotification", DEFAULT_SHOW_BOOT_NOTIFICATION))
        startup_card.add_widget(self.boot_notification_cb)

        general_layout.addWidget(startup_card)

        # Window Behavior card
        behavior_card = SettingsCardWidget("Window Behavior")
        self._settings_cards.append(behavior_card)

        self.lock_cb = self._create_checkbox_row("Lock Window Position", self.state_manager.state.get("positionLocked", DEFAULT_POSITION_LOCKED))
        behavior_card.add_widget(self.lock_cb)

        self.pin_cb = self._create_checkbox_row("Pin to Desktop Background", self.state_manager.state.get("pinnedToDesktop", DEFAULT_PINNED_TO_DESKTOP))
        behavior_card.add_widget(self.pin_cb)

        self.always_on_top_cb = self._create_checkbox_row("Always on Top", self.state_manager.state.get("alwaysOnTop", DEFAULT_ALWAYS_ON_TOP))
        behavior_card.add_widget(self.always_on_top_cb)

        self.pin_cb.toggled.connect(self._on_pin_to_desktop_toggled)
        self.always_on_top_cb.toggled.connect(self._on_always_on_top_toggled)

        general_layout.addWidget(behavior_card)

        general_layout.addStretch()

        general_layout.addStretch()

        # ── Appearance Tab (content) ──
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        appearance_layout.setContentsMargins(*MARGIN_SETTINGS_TAB)
        appearance_layout.setSpacing(SETTINGS_APPEARANCE_TAB_SPACING)

        # Theme
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("font-weight: 600;")
        appearance_layout.addWidget(theme_label)

        theme_cards_layout = QHBoxLayout()
        theme_cards_layout.setSpacing(SPACING_SM)
        self._theme_cards = {}
        saved_theme = normalize_theme_id(self.state_manager.state.get("theme", "dark"))
        for tid in ["dark", "light", "oled"]:
            colors = get_theme(tid)["colors"]
            card = ThemeCardWidget(tid, tid.capitalize(), colors)
            card.mousePressEvent = lambda _, t=tid: self._select_theme(t)
            theme_cards_layout.addWidget(card)
            self._theme_cards[tid] = card
        self._theme_cards[saved_theme].set_selected(True)
        for tid, card in self._theme_cards.items():
            card.update_theme(saved_theme)
        for card in getattr(self, '_settings_cards', []):
            card.update_theme(saved_theme)
        self._initial_theme = saved_theme
        theme_cards_layout.addStretch()
        appearance_layout.addLayout(theme_cards_layout)

        # Task text size — label shows live value
        text_size_row = QHBoxLayout()
        text_size_row.setSpacing(SPACING_MD)
        text_size_label_title = QLabel("Task text size")
        text_size_label_title.setStyleSheet("font-weight: 600;")
        text_size_row.addWidget(text_size_label_title)
        text_size_row.addStretch()
        self.text_size_label = QLabel()
        self.text_size_label.setStyleSheet("opacity: 0.7;")
        self.text_size_label.setMinimumWidth(SETTINGS_VALUE_LABEL_MIN_WIDTH)
        self.text_size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        text_size_row.addWidget(self.text_size_label)
        appearance_layout.addLayout(text_size_row)

        self.text_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.text_size_slider.setMinimum(10)
        self.text_size_slider.setMaximum(TEXT_SIZE_SLIDER_MAX)
        self.text_size_slider.setValue(int(self.state_manager.state.get("taskTextSize", FONT_SIZE_TITLE_MD)))
        self.text_size_slider.valueChanged.connect(self.update_text_size_label)
        self.text_size_slider.valueChanged.connect(self._mark_dirty)
        self.text_size_slider.valueChanged.connect(self._emit_text_size_to_parent)
        appearance_layout.addWidget(self.text_size_slider)
        self.update_text_size_label(self.text_size_slider.value())

        # Opacity — label shows live value
        opacity_row = QHBoxLayout()
        opacity_row.setSpacing(SPACING_MD)
        opacity_label = QLabel("Window opacity")
        opacity_label.setStyleSheet("font-weight: 600;")
        opacity_row.addWidget(opacity_label)
        opacity_row.addStretch()
        self.opacity_value_label = QLabel()
        self.opacity_value_label.setStyleSheet("opacity: 0.7;")
        self.opacity_value_label.setMinimumWidth(SETTINGS_VALUE_LABEL_MIN_WIDTH)
        self.opacity_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        opacity_row.addWidget(self.opacity_value_label)
        appearance_layout.addLayout(opacity_row)

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(OPACITY_SLIDER_MIN)
        self.opacity_slider.setMaximum(OPACITY_SLIDER_MAX)
        current_opacity = max(OPACITY_SLIDER_MIN, int(self.state_manager.state.get("opacity", 1.0) * OPACITY_DIVISOR))
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
        self.mouse_glow_toggle.setChecked(self.state_manager.state.get("mouseGlow", DEFAULT_MOUSE_GLOW))
        self.mouse_glow_toggle.toggled.connect(self._mark_dirty)
        self.mouse_glow_toggle.toggled.connect(self._on_mouse_glow_toggled)
        mouse_glow_row.addWidget(self.mouse_glow_toggle)
        appearance_layout.addLayout(mouse_glow_row)

        # Font family selection
        font_row = QHBoxLayout()
        font_row.setSpacing(SPACING_MD)
        font_label = QLabel("Task font")
        font_label.setStyleSheet("font-weight: 600;")
        font_row.addWidget(font_label)
        font_row.addStretch()
        appearance_layout.addLayout(font_row)

        self.font_combo = QComboBox()
        self.font_combo.addItems([
            "Default (System)",
            "Segoe UI",
            "Arial",
            "Helvetica",
            "Consolas",
            "Courier New",
            "Verdana",
            "Georgia",
            "Comic Sans MS",
        ])
        saved_font = self.state_manager.state.get("taskFont", DEFAULT_TASK_FONT)
        idx = self.font_combo.findText(saved_font)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)
        self.font_combo.currentTextChanged.connect(self._mark_dirty)
        self.font_combo.currentTextChanged.connect(self._on_font_changed)
        appearance_layout.addWidget(self.font_combo)

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
        shortcuts_layout.setContentsMargins(*MARGIN_SETTINGS_TAB)
        shortcuts_layout.setSpacing(SPACING_SM)

        def _add_section_label(text: str) -> None:
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: bold; padding-top: 4px;")
            shortcuts_layout.addWidget(lbl)

        def _add_shortcut_row(title: str, hint: str | None, default_seq: str, attr_name: str, state_key: str) -> None:
            card = QFrame()
            card.setObjectName("nestedPanel")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(*SETTINGS_SHORTCUT_CARD_MARGINS)
            card_layout.setSpacing(SPACING_MD)

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
            edit.setFixedWidth(KEY_SEQ_EDIT_WIDTH)
            edit.setToolTip("Click and press the desired key combination to record it")
            edit.setKeySequence(self._load_sequence(self.state_manager.state.get(state_key), default_seq))
            edit.keySequenceChanged.connect(self._mark_dirty)

            glow = QGraphicsDropShadowEffect(edit)
            glow.setBlurRadius(SETTINGS_GLOW_BLUR_RADIUS)
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
        _add_shortcut_row("Reminders", "Open pending task reminders.", "Alt+R",
                          "reminders_shortcut_edit", "remindersShortcut")

        shortcuts_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        shortcuts_outer_layout.addWidget(scroll_area)

        # ── Export Tab (content) ──
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        export_layout.setContentsMargins(*MARGIN_SETTINGS_TAB)
        export_layout.setSpacing(SPACING_MD)

        # ── Format section ──
        format_label = QLabel("Format")
        format_label.setStyleSheet(f"font-size: {FONT_SIZE_TITLE_MD}px; font-weight: bold;")
        export_layout.addWidget(format_label)
        self.export_format_combo = QComboBox()
        self.export_format_combo.setMinimumHeight(EXPORT_COMBO_HEIGHT)
        self.export_format_combo.addItem("Plain Text (.txt)", "txt")
        self.export_format_combo.addItem("Markdown (.md)", "md")
        self.export_format_combo.addItem("CSV (.csv)", "csv")
        export_layout.addWidget(self.export_format_combo)

        # ── Options section ──
        options_label = QLabel("Options")
        options_label.setStyleSheet(f"font-size: {FONT_SIZE_TITLE_MD}px; font-weight: bold;")
        export_layout.addWidget(options_label)
        self.export_include_history_cb = QCheckBox("Include history")
        self.export_include_history_cb.setChecked(False)
        self.export_include_history_cb.setStyleSheet(f"font-size: {FONT_SIZE_TITLE_MD}px;")
        self.export_include_history_cb.stateChanged.connect(self._mark_dirty)
        export_layout.addWidget(self.export_include_history_cb)

        # ── Group filter section (always created; visibility toggled by state) ──
        self._export_group_filter = {}  # groupId -> QCheckBox
        self._export_all_groups_cb: QCheckBox | None = None
        self._export_filter_label = QLabel("Groups to export")
        self._export_filter_label.setStyleSheet(f"font-size: {FONT_SIZE_TITLE_MD}px; font-weight: bold;")
        export_layout.addWidget(self._export_filter_label)

        self._export_filter_card = QFrame()
        self._export_filter_card.setObjectName("nestedPanel")
        card_layout = QVBoxLayout(self._export_filter_card)
        card_layout.setContentsMargins(8, 6, 8, 6)
        card_layout.setSpacing(2)

        self._export_all_groups_cb = QCheckBox("All groups")
        self._export_all_groups_cb.setChecked(True)
        self._export_all_groups_cb.setStyleSheet(f"font-size: {FONT_SIZE_TITLE_MD}px; font-weight: bold;")
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
        self._export_group_scroll.setMinimumHeight(SCROLL_AREA_MIN_HEIGHT)
        self._export_group_scroll.setMaximumHeight(SCROLL_AREA_MAX_HEIGHT)

        self._export_group_content = QWidget()
        self._export_group_content.setObjectName("transparentSurface")
        self._export_group_cl = QVBoxLayout(self._export_group_content)
        self._export_group_cl.setContentsMargins(*SETTINGS_EXPORT_GROUP_CONTENT_MARGINS)
        self._export_group_cl.setSpacing(3)

        self._export_group_scroll.setWidget(self._export_group_content)
        card_layout.addWidget(self._export_group_scroll)

        export_layout.addWidget(self._export_filter_card)

        self._populate_export_group_filter()
        self._update_export_groups_filter()

        export_layout.addStretch()

        self.export_btn = QPushButton("Export Tasks…")
        self.export_btn.setObjectName("primaryButton")
        self.export_btn.setMinimumHeight(BTN_HEIGHT_LG)
        self.export_btn.clicked.connect(self._run_settings_export)
        export_layout.addWidget(self.export_btn)

        # ── Advanced Tab (content) ──
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        advanced_layout.setContentsMargins(*MARGIN_SETTINGS_TAB)
        advanced_layout.setSpacing(SPACING_LG)

        self.groups_enabled_cb = self._create_checkbox_row(
            "Enable task groups",
            self.state_manager.state.get("groupsEnabled", DEFAULT_GROUPS_ENABLED),
        )
        advanced_layout.addWidget(self.groups_enabled_cb)

        self.tag_filter_cb = self._create_checkbox_row(
            "Enable tag filter bar",
            self.state_manager.state.get("tagFilterEnabled", DEFAULT_TAG_FILTER_ENABLED),
        )
        advanced_layout.addWidget(self.tag_filter_cb)

        self.completion_sound_cb = self._create_checkbox_row(
            "Play sound on task completion",
            self.state_manager.state.get("playCompletionSound", DEFAULT_PLAY_COMPLETION_SOUND),
        )
        advanced_layout.addWidget(self.completion_sound_cb)

        retention_row = QHBoxLayout()
        retention_label = QLabel("History retention:")
        set_label_point_size(retention_label, FONT_SIZE_LABEL_SM)
        retention_row.addWidget(retention_label)
        retention_row.addStretch()

        self.retention_combo = QComboBox()
        self.retention_combo.addItems([
            "5 days",
            "7 days",
            "14 days",
            "30 days",
            "60 days",
            "90 days",
            "6 months",
            "1 year",
            "Forever",
        ])
        retention_values = [5, 7, 14, 30, 60, 90, 180, 365, 0]
        saved_retention = self.state_manager.state.get("historyRetentionDays", DEFAULT_HISTORY_RETENTION_DAYS)
        try:
            idx = retention_values.index(saved_retention)
        except ValueError:
            idx = 3  # default to 30 days
        self.retention_combo.setCurrentIndex(idx)
        self.retention_combo.setMinimumWidth(KEY_SEQ_EDIT_WIDTH)
        retention_row.addWidget(self.retention_combo)
        advanced_layout.addLayout(retention_row)

        advanced_layout.addStretch()

        # ── Reminders Tab (content) ──
        reminders_tab = QWidget()
        reminders_layout = QVBoxLayout(reminders_tab)
        reminders_layout.setContentsMargins(*MARGIN_SETTINGS_TAB)
        reminders_layout.setSpacing(SPACING_LG)

        reminders_title = self._create_tab_label("Reminders")
        reminders_layout.addWidget(reminders_title)

        reminders_sep = QFrame()
        reminders_sep.setObjectName("hSeparator")
        reminders_sep.setFrameShape(QFrame.Shape.HLine)
        reminders_sep.setFixedHeight(1)
        reminders_layout.addWidget(reminders_sep)

        task_reminder_label = QLabel("Pending Task Reminders")
        set_label_point_size(task_reminder_label, FONT_SIZE_TITLE_MD)
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
        help_layout.setContentsMargins(*MARGIN_SETTINGS_TAB)
        help_layout.setSpacing(SPACING_LG)

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
        content_row.setSpacing(SPACING_MD)

        self._sidebar_layout = QVBoxLayout()
        self._sidebar_layout.setSpacing(SPACING_SM)
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
            btn.setFixedHeight(BTN_HEIGHT_LG)
            btn.setToolTip(f"Open {name} settings")
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))
            self._sidebar_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignLeft)
            self._page_buttons.append(btn)

        self._sidebar_layout.addStretch()

        right_column = QVBoxLayout()
        right_column.setSpacing(SPACING_MD)
        right_column.addWidget(self._stack, 1)

        # Reset to Defaults button - always visible above Save/Close
        self.reset_shortcuts_btn = QPushButton("Reset to Defaults")
        self.reset_shortcuts_btn.setObjectName("ghostButton")
        self.reset_shortcuts_btn.setMinimumHeight(BTN_HEIGHT_MD)
        self.reset_shortcuts_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_shortcuts_btn.clicked.connect(self._reset_active_tab_to_defaults)
        right_column.addWidget(self.reset_shortcuts_btn)

        button_row = QHBoxLayout()
        button_row.setSpacing(SPACING_MD)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setEnabled(False)
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

        last_tab = self.state_manager.state.get("lastSettingsTab", 0)
        if not isinstance(last_tab, int) or last_tab < 0 or last_tab >= self._stack.count():
            last_tab = 0
        self._switch_page(last_tab)

        self._saved_snapshot = self._build_snapshot()
        self._has_unsaved_changes = False
        self._initialized = True
        self._update_overlap_opacity()
        self._populate_task_reminder_list()
        self._apply_entry_widget_theming()

    def _apply_entry_widget_theming(self, theme_id=None):
        from PyQt6.QtWidgets import QScrollArea
        if theme_id is None:
            theme_id = self._get_theme_id()
        theme = get_theme(theme_id)
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
            sa.setStyleSheet(settings_scroll_area_stylesheet(theme))
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
            from src.frontend.theme import _style_all_combo_views, combo_popup_view_stylesheet
            view = w.view()
            if view:
                view_css = combo_popup_view_stylesheet(theme)
                view.setStyleSheet(view_css)
                popup_win = view.window()
                if popup_win is not None:
                    popup_win.setStyleSheet(view_css)
        _style_all_combo_views(theme)

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
        self.state_manager.state["lastSettingsTab"] = index

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
            cb.setStyleSheet(f"font-size: {FONT_SIZE_TITLE_MD}px;")
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
        opacity = self.opacity_slider.value() / OPACITY_DIVISOR
        self.state_manager.state["opacity"] = opacity
        self.state_manager.state["taskTextSize"] = self.text_size_slider.value()
        self.state_manager.state["taskFont"] = self.font_combo.currentText()
        self.state_manager.state["mouseGlow"] = self.mouse_glow_toggle.isChecked()
        self.state_manager.state["historyShortcut"] = self.history_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Ctrl+H"
        self.state_manager.state["settingsShortcut"] = self.settings_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Ctrl+,"
        self.state_manager.state["pinShortcut"] = self.pin_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Ctrl+P"
        self.state_manager.state["toggleTrayShortcut"] = self.toggle_tray_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Ctrl+M"
        self.state_manager.state["alwaysOnTopShortcut"] = self.always_on_top_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Alt+T"
        self.state_manager.state["exportShortcut"] = self.export_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Ctrl+E"
        self.state_manager.state["remindersShortcut"] = self.reminders_shortcut_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "Alt+R"
        parent = self.parent()
        old_groups_enabled = parent.app_state.get("groupsEnabled", True) if (parent is not None and hasattr(parent, "task_row_widgets")) else True
        self.state_manager.state["groupsEnabled"] = self.groups_enabled_cb.isChecked()
        self.state_manager.state["tagFilterEnabled"] = self.tag_filter_cb.isChecked()
        self.state_manager.state["playCompletionSound"] = self.completion_sound_cb.isChecked()
        self.state_manager.state["historyRetentionDays"] = [5, 7, 14, 30, 60, 90, 180, 365, 0][self.retention_combo.currentIndex()]
        self.state_manager.state["checkForUpdates"] = self.check_updates_cb.isChecked()
        self.state_manager.state["showBootNotification"] = self.boot_notification_cb.isChecked()
        self.state_manager.save()
        self._saved_snapshot = self._build_snapshot()
        self._has_unsaved_changes = False
        self.save_btn.setEnabled(False)

        if parent is not None and hasattr(parent, '_shortcut_manager'):
            parent._shortcut_manager.update_shortcuts()

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
                parent.task_text_size = int(self.state_manager.state.get("taskTextSize", FONT_SIZE_TITLE_MD))
                for row in parent.task_row_widgets.values():
                    if hasattr(row, "set_text_size"):
                        row.set_text_size(parent.task_text_size)
                parent._sync_task_row_text_layouts()
            # Apply tag filter toggle immediately
            if hasattr(parent, "_update_empty_state"):
                parent._update_empty_state()
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
            parent.setWindowOpacity(value / OPACITY_DIVISOR)
        self._auto_save_appearance()

    def _emit_text_size_to_parent(self, value):
        parent = self.parent()
        if parent is not None and hasattr(parent, "task_text_size"):
            parent.task_text_size = value
            parent.state_manager.state["taskTextSize"] = value
            if hasattr(parent, "render_tasks"):
                parent.render_tasks()
        self._auto_save_appearance()

    def _on_mouse_glow_toggled(self, checked):
        parent = self.parent()
        if parent is not None and hasattr(parent, '_glow_overlay'):
            if not checked:
                parent._glow_overlay.hide_glow()
            parent.app_state["mouseGlow"] = checked
        self._auto_save_appearance()

    def _on_font_changed(self, font_name):
        """Apply font change live to all task rows."""
        parent = self.parent()
        if parent is not None and hasattr(parent, 'task_row_widgets'):
            for row in parent.task_row_widgets.values():
                if hasattr(row, 'set_task_font'):
                    row.set_task_font(font_name)
        self._auto_save_appearance()

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
