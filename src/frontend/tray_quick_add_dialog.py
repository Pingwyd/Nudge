"""Quick Add dialog with group selection for tray-based task entry."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from src.backend.task_groups import create_group, sorted_groups
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.themed_input_dialog import ThemedInputDialog
from src.frontend.theme import get_theme, normalize_theme_id
from src.constants import (
    RADIUS_PANEL,
    FONT_SIZE_BODY,
    FONT_SIZE_LABEL_MD,
)


class TrayQuickAddDialog(GlassPanelDialog):
    """Floating quick-add dialog with group dropdown and task input."""

    def __init__(
        self,
        groups_data: dict,
        group_store,
        active_group_id: str,
        app_state: dict,
        parent=None,
    ):
        super().__init__(parent, overlap_radius=RADIUS_PANEL, escape_action="reject")
        self._groups_data = groups_data
        self._group_store = group_store
        self._app_state = app_state

        self.setWindowTitle("Quick Add")
        self.resize(280, 180)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title = QLabel("Quick Add")
        f = title.font()
        f.setPointSize(FONT_SIZE_LABEL_MD)
        f.setBold(True)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        groups_enabled = app_state.get("groupsEnabled", False)
        if groups_enabled:
            group_row = QHBoxLayout()
            group_row.setSpacing(6)

            group_label = QLabel("Group:")
            fl = group_label.font()
            fl.setPointSize(FONT_SIZE_BODY)
            group_label.setFont(fl)
            group_row.addWidget(group_label)

            self._group_combo = QComboBox()
            self._group_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self._populate_combo(active_group_id)
            group_row.addWidget(self._group_combo, 1)

            add_btn = QPushButton("+")
            add_btn.setFixedSize(22, 22)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.clicked.connect(self._on_add_group)
            group_row.addWidget(add_btn)

            layout.addLayout(group_row)

        self._input = QLineEdit()
        self._input.setPlaceholderText("New task...")
        self._input.setMinimumHeight(26)
        self._input.returnPressed.connect(self._on_return_pressed)
        layout.addWidget(self._input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch(1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(64, 24)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._add_btn = QPushButton("Add")
        self._add_btn.setFixedSize(64, 24)
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setEnabled(False)
        self._add_btn.setDefault(True)
        self._add_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._add_btn)

        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self._input.textChanged.connect(self._on_text_changed)
        self._apply_button_theme()
        self._input.setFocus()

    def _apply_always_on_top(self):
        if self._app_state.get("alwaysOnTop", False):
            flags = self.windowFlags()
            flags |= Qt.WindowType.WindowStaysOnTopHint
            self.setWindowFlags(flags)

    def _apply_button_theme(self) -> None:
        theme_id = self._get_theme_id()
        theme = get_theme(theme_id)
        c = theme["colors"]
        btn_css = f"""
            QPushButton {{
                border: 1px solid {c.get('border', 'rgba(255,255,255,60)')};
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                background: transparent;
                color: {c.get('text', '#ffffff')};
            }}
            QPushButton:hover {{
                background: {c.get('hover', 'rgba(255,255,255,40)')};
                border: 1px solid {c.get('border_highlight', 'rgba(255,255,255,90)')};
            }}
            QPushButton:pressed {{
                background: {c.get('hover_strong', 'rgba(255,255,255,45)')};
            }}
            QPushButton:disabled {{
                color: {c.get('text_muted', 'rgba(255,255,255,180)')};
                border: 1px solid {c.get('border', 'rgba(255,255,255,60)')};
            }}
        """
        self.setStyleSheet(btn_css)

    def _populate_combo(self, active_group_id: str) -> None:
        self._group_combo.blockSignals(True)
        self._group_combo.clear()
        for group in sorted_groups(self._groups_data):
            self._group_combo.addItem(group["name"], group["id"])
        idx = self._group_combo.findData(active_group_id)
        if idx >= 0:
            self._group_combo.setCurrentIndex(idx)
        self._group_combo.blockSignals(False)

    def _on_add_group(self) -> None:
        dlg = ThemedInputDialog(None, title="New Group", label="Group name:")
        if not dlg.exec() == QDialog.DialogCode.Accepted:
            return
        name = dlg.get_text().strip()
        if not name:
            return
        order = len(self._groups_data.get("groups", []))
        new_group = create_group(name, order)
        self._groups_data["groups"].append(new_group)
        self._group_store.save(self._groups_data)
        self._populate_combo(new_group["id"])

    def _on_text_changed(self, text: str) -> None:
        self._add_btn.setEnabled(bool(text.strip()))

    def _on_return_pressed(self) -> None:
        if self._input.text().strip():
            self.accept()

    def get_text(self) -> str:
        return self._input.text()

    def get_selected_group_id(self) -> str:
        if hasattr(self, '_group_combo'):
            gid = self._group_combo.currentData()
            return gid if gid else "general"
        return "general"
