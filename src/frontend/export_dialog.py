"""
Export options dialog (Stage 10).
"""

from __future__ import annotations

from pathlib import Path

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
    QDialog,
)

from src.backend.export_service import ExportFormat, ExportRequest, export_to_file, file_filter_for_format
from src.backend.icon import get_app_icon
from src.backend.task_groups import sorted_groups
from src.frontend.themed_message_dialog import ThemedMessageDialog
from src.frontend.theme import (
    get_theme,
    glass_overlap_stylesheet,
    normalize_theme_id,
    refresh_glass_shells,
)


def _set_label_point_size(label: QLabel, point_size: int, bold: bool = False) -> None:
    font = label.font()
    font.setPointSize(point_size)
    font.setBold(bold)
    label.setFont(font)


class ExportDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.text_size = int(main_window.app_state.get("taskTextSize", 14))
        self._drag_pos = None
        self.frame = None
        self._export_group_filter: dict[str, QCheckBox] = {}
        self._export_all_groups_cb: QCheckBox | None = None
        self._export_group_bulk_update = False
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Export Tasks")
        self.setWindowIcon(get_app_icon())
        screen = self.screen() or (QApplication.primaryScreen() if QApplication.instance() else None)
        if screen:
            available = screen.availableGeometry()
            max_h = available.height() - 80
            max_w = available.width() - 80
            w = min(380, max_w)
            h = min(420, max_h)
        else:
            w, h = 380, 420
        self.resize(w, h)
        self.setMinimumSize(320, 360)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.frame = QFrame(self)
        self.frame.setObjectName("glassPanel")
        self.frame.setGeometry(0, 0, w, h)

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

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
        self.format_combo.setMinimumHeight(26)
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
            card_layout.setContentsMargins(8, 6, 8, 6)
            card_layout.setSpacing(2)

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
            group_scroll.setMinimumHeight(36)
            group_scroll.setMaximumHeight(110)

            group_content = QWidget()
            group_content.setObjectName("transparentSurface")
            group_cl = QVBoxLayout(group_content)
            group_cl.setContentsMargins(14, 4, 4, 4)
            group_cl.setSpacing(3)

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
        buttons.setSpacing(8)
        export_btn = QPushButton("Choose file…")
        export_btn.setObjectName("primaryButton")
        export_btn.setMinimumHeight(32)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.setDefault(True)
        export_btn.clicked.connect(self._run_export)
        buttons.addWidget(export_btn, 1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.setMinimumHeight(32)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn, 1)
        layout.addLayout(buttons)

        self._update_overlap_opacity()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            event.accept()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        if self.frame is not None:
            self.frame.setGeometry(self.rect())
        super().resizeEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self._update_overlap_opacity()

    def _update_overlap_opacity(self):
        parent = self.parent()
        if parent is None or not isinstance(parent, QMainWindow):
            return
        overlap = self.frameGeometry().intersects(parent.frameGeometry())
        if overlap:
            theme_id = normalize_theme_id(self.main_window.app_state.get("theme", "dark"))
            theme = get_theme(theme_id)
            self.frame.setStyleSheet(glass_overlap_stylesheet(theme, radius=20))
        else:
            theme_id = normalize_theme_id(self.main_window.app_state.get("theme", "dark"))
            refresh_glass_shells(self, theme_id)

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
        export_format = self._selected_format()
        label, extension = file_filter_for_format(export_format)
        last_dir = self.main_window.state_manager.state.get("lastExportDir", "")
        initial = str(Path(last_dir) / f"tasks_export{extension}") if last_dir else f"tasks_export{extension}"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Tasks",
            initial,
            f"{label};;All Files (*.*)",
        )
        if not filepath:
            return

        path = Path(filepath).resolve()
        if path.suffix.lower() != extension:
            path = path.with_suffix(extension)

        if self._export_group_filter and not self._export_all_groups_cb.isChecked():
            selected = {gid for gid, cb in self._export_group_filter.items() if cb.isChecked()}
            if selected:
                active_filtered = [t for t in self.main_window.tasks if t.get("groupId") in selected]
                history_raw = self.main_window.history_store.load()
                history_filtered = [t for t in history_raw if t.get("groupId") in selected]
            else:
                active_filtered = list(self.main_window.tasks)
                history_filtered = self.main_window.history_store.load()
        else:
            active_filtered = list(self.main_window.tasks)
            history_filtered = self.main_window.history_store.load()

        request = ExportRequest(
            filepath=path,
            export_format=export_format,
            include_history=self.include_history_cb.isChecked(),
            active_tasks=active_filtered,
            history_tasks=history_filtered,
            groups_doc=self.main_window.groups_data,
        )

        try:
            export_to_file(request)
        except OSError as error:
            ThemedMessageDialog.warning(self, "Export Failed", f"Could not write file:\n{error}")
            return

        self.main_window.state_manager.state["lastExportDir"] = str(path.parent)
        self.main_window.state_manager.save()

        if ThemedMessageDialog.question(
            self,
            "Export Complete",
            f"Tasks exported successfully to:\n{path}\n\nDo you want to open the file location?",
            yes_label="Open file location",
            no_label="Close",
        ):
            import os
            os.startfile(str(path.parent))
        self.accept()
