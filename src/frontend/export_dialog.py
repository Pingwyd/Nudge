"""
Export options dialog (Stage 10).
"""

from __future__ import annotations

from pathlib import Path

from src.os_layer.platform_utils import open_file_explorer

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.backend.export_service import ExportFormat, ExportRequest, export_to_file, file_filter_for_format
from src.backend.icon import get_app_icon
from src.backend.task_groups import sorted_groups
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.themed_message_dialog import ThemedMessageDialog
from src.frontend.theme import (
    get_theme,
    glass_overlap_stylesheet,
    normalize_theme_id,
    refresh_glass_shells,
)
from src.constants import (
    BTN_HEIGHT_LG,
    EXPORT_COMBO_HEIGHT,
    EXPORT_DIALOG_DEFAULT,
    EXPORT_DIALOG_MIN,
    EXPORT_GROUP_CARD_MARGINS,
    EXPORT_GROUP_CARD_SPACING,
    EXPORT_GROUP_CHECKBOX_SPACING,
    EXPORT_GROUP_LIST_MARGINS,
    EXPORT_GROUP_SCROLL_MAX,
    EXPORT_GROUP_SCROLL_MIN,
    EXPORT_SCREEN_EDGE_MARGIN,
    MARGIN_WIDE,
    SCROLL_AREA_MIN_HEIGHT,
    SPACING_MD,
)


class ExportDialog(GlassPanelDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.text_size = int(main_window.app_state.get("taskTextSize", 14))
        self._export_group_filter: dict[str, QCheckBox] = {}
        self._export_all_groups_cb: QCheckBox | None = None
        self._export_group_bulk_update = False
        self._init_ui()

    def _get_theme_id(self) -> str:
        return normalize_theme_id(self.main_window.app_state.get("theme", "dark"))

    def _init_ui(self):
        self.setWindowTitle("Export Tasks")
        self.setWindowIcon(get_app_icon())
        screen = self.screen() or (QApplication.primaryScreen() if QApplication.instance() else None)
        if screen:
            available = screen.availableGeometry()
            max_h = available.height() - EXPORT_SCREEN_EDGE_MARGIN
            max_w = available.width() - EXPORT_SCREEN_EDGE_MARGIN
            w = min(EXPORT_DIALOG_DEFAULT[0], max_w)
            h = min(EXPORT_DIALOG_DEFAULT[1], max_h)
        else:
            w, h = EXPORT_DIALOG_DEFAULT
        self.resize(w, h)
        self.setMinimumSize(*EXPORT_DIALOG_MIN)

        self.bg_frame.setGeometry(0, 0, w, h)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*MARGIN_WIDE)
        layout.setSpacing(SPACING_MD)

        # ── Title ──
        title = QLabel("Export Tasks")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold;")
        layout.addWidget(title)

        # ── Format section ──
        format_label = QLabel("Format")
        format_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(format_label)

        self.format_combo = QComboBox()
        self.format_combo.setMinimumHeight(EXPORT_COMBO_HEIGHT)
        self.format_combo.addItem("Plain Text (.txt)", "txt")
        self.format_combo.addItem("Markdown (.md)", "md")
        self.format_combo.addItem("CSV (.csv)", "csv")
        layout.addWidget(self.format_combo)

        # ── Options section ──
        options_label = QLabel("Options")
        options_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(options_label)

        self.include_history_cb = QCheckBox("Include history")
        self.include_history_cb.setChecked(False)
        layout.addWidget(self.include_history_cb)

        # ── Group filter section ──
        groups_enabled = self.main_window.app_state.get("groupsEnabled", True)
        groups_data = self.main_window.groups_data
        all_groups = sorted_groups(groups_data) if groups_data else []
        has_filter = groups_enabled and len(all_groups) > 1
        if has_filter:
            flt_label = QLabel("Groups to export")
            flt_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(flt_label)

            group_card = QFrame()
            group_card.setObjectName("nestedPanel")
            card_layout = QVBoxLayout(group_card)
            card_layout.setContentsMargins(*EXPORT_GROUP_CARD_MARGINS)
            card_layout.setSpacing(EXPORT_GROUP_CARD_SPACING)

            self._export_all_groups_cb = QCheckBox("All groups")
            self._export_all_groups_cb.setChecked(True)
            self._export_all_groups_cb.setStyleSheet("font-weight: bold;")
            self._export_all_groups_cb.toggled.connect(self._on_export_all_groups_toggled)
            card_layout.addWidget(self._export_all_groups_cb)

            sep = QFrame()
            sep.setObjectName("hSeparator")
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setFixedHeight(1)
            card_layout.addWidget(sep)

            group_scroll = QScrollArea()
            group_scroll.setWidgetResizable(True)
            group_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            group_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            group_scroll.setStyleSheet("border: none; background: transparent;")
            group_scroll.setMinimumHeight(EXPORT_GROUP_SCROLL_MIN)
            group_scroll.setMaximumHeight(EXPORT_GROUP_SCROLL_MAX)

            group_content = QWidget()
            group_content.setObjectName("transparentSurface")
            group_cl = QVBoxLayout(group_content)
            group_cl.setContentsMargins(*EXPORT_GROUP_LIST_MARGINS)
            group_cl.setSpacing(EXPORT_GROUP_CHECKBOX_SPACING)

            for g in all_groups:
                cb = QCheckBox(g["name"])
                cb.setChecked(True)
                cb.stateChanged.connect(self._on_export_group_changed)
                self._export_group_filter[g["id"]] = cb
                group_cl.addWidget(cb)

            group_cl.addStretch()
            group_content.setLayout(group_cl)
            group_scroll.setWidget(group_content)
            card_layout.addWidget(group_scroll)

            layout.addWidget(group_card)

        layout.addStretch()

        # ── Action buttons ──
        buttons = QHBoxLayout()
        buttons.setSpacing(SPACING_MD)
        export_btn = QPushButton("Choose file…")
        export_btn.setObjectName("primaryButton")
        export_btn.setMinimumHeight(BTN_HEIGHT_LG)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.setDefault(True)
        export_btn.clicked.connect(self._run_export)
        buttons.addWidget(export_btn, 1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.setMinimumHeight(BTN_HEIGHT_LG)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn, 1)
        layout.addLayout(buttons)

        self._update_overlap_opacity()

    def _selected_format(self) -> ExportFormat:
        value = self.format_combo.currentData()
        return value if value in ("txt", "md", "csv") else "txt"

    def _on_export_all_groups_toggled(self, checked: bool):
        if getattr(self, "_export_group_bulk_update", False):
            return
        self._export_group_bulk_update = True
        try:
            for cb in self._export_group_filter.values():
                cb.setChecked(checked)
        finally:
            self._export_group_bulk_update = False
        self._export_all_groups_cb.blockSignals(True)
        self._export_all_groups_cb.setChecked(checked)
        self._export_all_groups_cb.blockSignals(False)

    def _on_export_group_changed(self):
        if getattr(self, "_export_group_bulk_update", False):
            return
        all_checked = all(cb.isChecked() for cb in self._export_group_filter.values())
        self._export_all_groups_cb.blockSignals(True)
        self._export_all_groups_cb.setChecked(all_checked)
        self._export_all_groups_cb.blockSignals(False)

    def _run_export(self):
        from src.backend.export_service import run_export_with_dialog

        export_format = self._selected_format()
        success = run_export_with_dialog(
            parent_widget=self,
            main_window=self.main_window,
            export_format=export_format,
            include_history=self.include_history_cb.isChecked(),
            group_filter=self._export_group_filter,
            all_groups_checked=self._export_all_groups_cb.isChecked() if self._export_all_groups_cb else True,
        )
        if success:
            self.accept()
