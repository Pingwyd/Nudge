"""Task search bar with amber accent icon and optional scope filter chips."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.constants import (
    DIALOG_BORDER_WIDTH,
    FONT_SIZE_BODY,
    FONT_SIZE_LABEL_SM,
    RADIUS_BUTTON,
    SPACING_MD,
    SPACING_SM,
)

_SEARCH_SCOPES = ("tasks", "groups", "tags")
_SCOPE_LABELS = {"tasks": "Tasks", "groups": "Groups", "tags": "Tags"}


class TaskSearchBar(QFrame):
    search_changed = pyqtSignal(str)
    filters_changed = pyqtSignal(set)  # active scope ids
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("taskSearchBar")
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._emit_search)
        self._safe_parent = None
        self._suppress_focus_close = False
        self._active_scopes = set(_SEARCH_SCOPES)
        self._chip_buttons: dict[str, QPushButton] = {}
        self._theme = None
        self._setup_ui()
        self.hide()

    def set_safe_parent(self, widget):
        """Set a parent widget whose children should not auto-close the bar."""
        self._safe_parent = widget

    def suppress_next_focus_close(self) -> None:
        """Ignore the next FocusOut close (e.g. user clicked the search toggle)."""
        self._suppress_focus_close = True

    def active_scopes(self) -> set[str]:
        return set(self._active_scopes)

    def set_has_results(self, has_results: bool) -> None:
        """Chips appear only once a query has produced results."""
        querying = bool(self._input.text().strip())
        self._chips_row.setVisible(querying and has_results)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACING_MD, SPACING_SM, SPACING_MD, SPACING_SM)
        root.setSpacing(SPACING_SM)

        row = QHBoxLayout()
        row.setSpacing(SPACING_SM)

        self._icon_btn = QToolButton()
        self._icon_btn.setObjectName("searchBarIcon")
        self._icon_btn.setFixedSize(22, 22)
        self._icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._icon_btn.setToolTip("Close search")
        self._icon_btn.setAutoRaise(True)
        self._icon_btn.clicked.connect(self.close_requested.emit)
        row.addWidget(self._icon_btn)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Search tasks, groups, tags...")
        self._input.setClearButtonEnabled(True)
        self._input.installEventFilter(self)
        self._input.textChanged.connect(self._debounce_search)
        self._input.returnPressed.connect(self._emit_search)
        row.addWidget(self._input, 1)
        root.addLayout(row)

        self._chips_row = QWidget()
        chips_lay = QHBoxLayout(self._chips_row)
        chips_lay.setContentsMargins(0, 0, 0, 0)
        chips_lay.setSpacing(6)
        for scope in _SEARCH_SCOPES:
            btn = QPushButton(_SCOPE_LABELS[scope])
            btn.setObjectName("searchScopeChip")
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, s=scope: self._on_chip_toggled(s, checked))
            chips_lay.addWidget(btn)
            self._chip_buttons[scope] = btn
        chips_lay.addStretch()
        self._chips_row.hide()
        root.addWidget(self._chips_row)

    def _on_chip_toggled(self, scope: str, checked: bool) -> None:
        if checked:
            self._active_scopes.add(scope)
        else:
            self._active_scopes.discard(scope)
        # Keep at least one scope active
        if not self._active_scopes:
            self._active_scopes.add(scope)
            self._chip_buttons[scope].setChecked(True)
        self._style_chips()
        self.filters_changed.emit(self.active_scopes())

    def eventFilter(self, obj, event):
        if obj == self._input and event.type() == QEvent.Type.FocusOut:
            QTimer.singleShot(150, self._check_focus)
        return super().eventFilter(obj, event)

    def _check_focus(self):
        if self._suppress_focus_close:
            self._suppress_focus_close = False
            return
        if not self.isVisible():
            return
        focus_widget = self.window().focusWidget()
        if focus_widget in (self._input, self, self._icon_btn) or focus_widget in self._chip_buttons.values():
            return
        if focus_widget and focus_widget.parent() is self._chips_row:
            return
        if focus_widget and self._safe_parent is not None:
            p = focus_widget
            while p:
                if p is self._safe_parent:
                    return
                p = p.parent()
        self.close_requested.emit()

    def _debounce_search(self, text):
        if not text.strip():
            self._chips_row.hide()
        self._search_timer.start(80)

    def _emit_search(self):
        self._search_timer.stop()
        self.search_changed.emit(self._input.text().strip())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close_requested.emit()
        else:
            super().keyPressEvent(event)

    def activate(self):
        self._suppress_focus_close = False
        self._active_scopes = set(_SEARCH_SCOPES)
        for scope, btn in self._chip_buttons.items():
            btn.setChecked(True)
        self._style_chips()
        self._chips_row.hide()
        self.show()
        self._input.clear()
        self._input.setFocus()

    def deactivate(self):
        self.hide()
        self._chips_row.hide()
        self._input.clear()
        self.search_changed.emit("")

    def _style_chips(self) -> None:
        if self._theme is None:
            return
        c = self._theme["colors"]
        accent = c.get("accent", "#F5A623")
        on_accent = c.get("on_accent", "#1A1205")
        muted = c.get("text_muted", "rgba(255,255,255,180)")
        inactive_bg = c.get("tab_bg", "rgba(255,255,255,20)")
        for scope, btn in self._chip_buttons.items():
            if btn.isChecked():
                # Amber tinted active chip (mock)
                btn.setStyleSheet(
                    f"""
                    QPushButton#searchScopeChip {{
                        background: rgba(245, 166, 35, 40);
                        color: {accent};
                        border: none;
                        border-radius: 10px;
                        padding: 3px 10px;
                        font-size: {FONT_SIZE_LABEL_SM}px;
                        font-weight: 600;
                    }}
                    """
                )
            else:
                btn.setStyleSheet(
                    f"""
                    QPushButton#searchScopeChip {{
                        background: {inactive_bg};
                        color: {muted};
                        border: none;
                        border-radius: 10px;
                        padding: 3px 10px;
                        font-size: {FONT_SIZE_LABEL_SM}px;
                        font-weight: 500;
                    }}
                    """
                )

    def apply_theme(self, theme):
        from src.frontend.theme import search_icon_pixmap

        self._theme = theme
        bg = theme["colors"].get("input_bg", "#2a2a2a")
        border = theme["colors"].get("border", "rgba(255,255,255,50)")
        text = theme["colors"].get("text", "#ffffff")
        placeholder = theme["colors"].get("text_muted", "#888888")
        hover = theme["colors"].get("hover", "rgba(255,255,255,40)")

        self.setStyleSheet(
            f"""
            QFrame#taskSearchBar {{
                background: {bg};
                border: {DIALOG_BORDER_WIDTH}px solid {border};
                border-radius: {RADIUS_BUTTON}px;
            }}
            QToolButton#searchBarIcon {{
                background: transparent;
                border: none;
                padding: 2px;
            }}
            QToolButton#searchBarIcon:hover {{
                background: {hover};
                border-radius: 4px;
            }}
        """
        )
        self._input.setStyleSheet(
            f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {text};
                font-size: {FONT_SIZE_BODY}px;
                padding: 4px 0;
            }}
            QLineEdit::placeholder {{
                color: {placeholder};
            }}
        """
        )
        self._icon_btn.setIcon(QIcon(search_icon_pixmap(theme, 16)))
        self._style_chips()
