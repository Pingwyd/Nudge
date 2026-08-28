"""TagFilterDropdown for filtering tasks by tag."""

from PyQt6.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPushButton,
                             QWidget)

from src.frontend.tag_pill_widget import get_tag_color
from src.frontend.theme import combo_popup_view_stylesheet, get_theme, normalize_theme_id


class _PopupStyler(QObject):
    """Restyle the combo popup every time it opens."""

    def __init__(self, css: str, bg: str, text: str, hover: str, parent=None):
        super().__init__(parent)
        self._css = css
        self._bg = bg
        self._text = text
        self._hover = hover

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show:
            from PyQt6.QtGui import QColor, QPalette

            # obj is the popup window — apply palette + CSS here
            pal = obj.palette()
            pal.setColor(QPalette.ColorRole.Highlight, QColor(self._hover))
            pal.setColor(QPalette.ColorRole.HighlightedText, QColor(self._text))
            pal.setColor(QPalette.ColorRole.Base, QColor(self._bg))
            obj.setPalette(pal)
            obj.setStyleSheet(self._css)
        return False


class _ThemedComboBox(QComboBox):
    """QComboBox that installs a popup styler on first showPopup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup_styler: _PopupStyler | None = None
        self._view_css = ""
        self._bg = ""
        self._text = ""
        self._hover = ""

    def set_popup_style(self, css: str, bg: str, text: str, hover: str):
        self._view_css = css
        self._bg = bg
        self._text = text
        self._hover = hover

    def showPopup(self):
        super().showPopup()
        popup_win = self.view().window()
        if popup_win and self._popup_styler is None:
            self._popup_styler = _PopupStyler(
                self._view_css, self._bg, self._text, self._hover, popup_win
            )
            popup_win.installEventFilter(self._popup_styler)
        if self._popup_styler:
            self._popup_styler._css = self._view_css
            self._popup_styler._bg = self._bg
            self._popup_styler._text = self._text
            self._popup_styler._hover = self._hover
        # Apply palette on both view and popup window
        from PyQt6.QtGui import QColor, QPalette
        for w in (self.view(), popup_win):
            if w is None:
                continue
            pal = w.palette()
            pal.setColor(QPalette.ColorRole.Highlight, QColor(self._hover))
            pal.setColor(QPalette.ColorRole.HighlightedText, QColor(self._text))
            pal.setColor(QPalette.ColorRole.Base, QColor(self._bg))
            w.setPalette(pal)
        if popup_win:
            popup_win.setStyleSheet(self._view_css)


class TagFilterDropdown(QWidget):
    """Compact tag filter with dropdown for selecting tags to filter by."""

    tags_selected = pyqtSignal(list)  # Emits list of selected tag names

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_tags: list[str] = []
        self._selected_tags: set[str] = set()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Filter icon/label
        self._filter_label = QLabel("Filter:")
        self._filter_label.setStyleSheet("font-size: 11px; opacity: 0.7;")
        layout.addWidget(self._filter_label)

        # Dropdown combo
        self._combo = _ThemedComboBox()
        self._combo.setMinimumWidth(100)
        self._combo.setMaximumWidth(160)
        self._combo.setPlaceholderText("All tags")
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self._combo)

        # Clear button (shown when filter active)
        self._clear_btn = QPushButton("\u2715")
        self._clear_btn.setFixedSize(22, 22)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setToolTip("Clear filter")
        self._clear_btn.clicked.connect(self.clear_filter)
        self._clear_btn.hide()
        layout.addWidget(self._clear_btn)
        
        self._apply_glass_style()

    def update_tags(self, tasks: list[dict]):
        """Update the available tags from the task list."""
        tags = set()
        for task in tasks:
            for tag in task.get("tags", []):
                tags.add(tag)
        self._all_tags = sorted(tags)
        self._rebuild_combo()

    def _rebuild_combo(self):
        """Rebuild the combo box items."""
        self._combo.blockSignals(True)
        self._combo.clear()

        # "All" option
        self._combo.addItem("All tags", None)

        for tag in self._all_tags:
            self._combo.addItem(tag, tag)

        # Restore selection
        if self._selected_tags:
            for i in range(self._combo.count()):
                if self._combo.itemData(i) in self._selected_tags:
                    self._combo.setCurrentIndex(i)
                    break
        else:
            self._combo.setCurrentIndex(0)

        self._combo.blockSignals(False)

    def _on_selection_changed(self, index):
        """Handle combo selection change."""
        tag = self._combo.currentData()
        if tag is None:
            self._selected_tags.clear()
            self._clear_btn.hide()
        else:
            self._selected_tags = {tag}
            self._clear_btn.show()
        self.tags_selected.emit(list(self._selected_tags))

    def clear_filter(self):
        """Clear the current filter."""
        self._selected_tags.clear()
        self._combo.setCurrentIndex(0)
        self._clear_btn.hide()
        self.tags_selected.emit([])

    def get_selected_tags(self) -> list[str]:
        """Return currently selected tags."""
        return list(self._selected_tags)

    def update_theme(self, theme_id: str = None):
        """Update styling based on theme."""
        if theme_id is None:
            theme_id = normalize_theme_id("dark")
        theme = get_theme(theme_id)
        colors = theme["colors"]

        bg = colors.get("glass_overlap_solid", colors.get("menu_bg", "rgba(18, 18, 18, 255)"))
        border = colors.get("border", "rgba(255, 255, 255, 60)")
        text = colors.get("text", "white")
        hover = colors.get("hover", "rgba(255, 255, 255, 0.15)")
        input_r = 6

        view_css = combo_popup_view_stylesheet(theme)

        # Pass popup style to the themed combo — it applies on every showPopup
        self._combo.set_popup_style(view_css, bg, text, hover)

        self.setStyleSheet(f"""
            TagFilterDropdown {{
                background: transparent;
            }}
            QLabel {{
                color: {text};
                opacity: 0.7;
                background: transparent;
            }}
            QComboBox {{
                background: {bg};
                border: 1px solid {border};
                border-radius: {input_r}px;
                padding: 4px 8px;
                color: {text};
                font-size: 11px;
            }}
            QComboBox:hover {{
                background: {hover};
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QPushButton {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 11px;
                color: {text};
                font-size: 11px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: rgba(255, 80, 80, 0.3);
                border: 1px solid rgba(255, 80, 80, 0.5);
                color: #ff5050;
            }}
        """)

    def _apply_glass_style(self):
        """Apply glass theme styling to match main app."""
        self.update_theme()
