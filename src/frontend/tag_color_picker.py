"""Inline floating color palette for tag colors."""

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QWidget

from src.frontend.tag_pill_widget import TAG_COLORS

# Module-level singleton reference
_active_popup = None
_focus_connected = False


def _on_app_focus_changed(old_widget, new_widget):
    """Close popup when anything outside it gains focus."""
    global _active_popup
    if _active_popup is None or not _active_popup.isVisible():
        return
    # new_widget is None when clicking outside the app entirely
    if new_widget is None:
        _active_popup.close()
        return
    # If the new focus target is not inside the popup, close it
    if not _active_popup.isAncestorOf(new_widget):
        _active_popup.close()


class ColorDot(QPushButton):
    """Small color circle for inline palette."""

    color_selected = pyqtSignal(str)

    def __init__(self, color: str, is_current: bool = False, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        border = "2px solid white" if is_current else "1px solid rgba(255,255,255,0.15)"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                border-radius: 8px;
                border: {border};
                padding: 0px;
                margin: 0px;
                min-width: 16px;
                max-width: 16px;
                min-height: 16px;
                max-height: 16px;
            }}
            QPushButton:hover {{
                border: 2px solid rgba(255,255,255,0.8);
            }}
        """)
        self.clicked.connect(lambda: self.color_selected.emit(color))


class TagColorPopup(QWidget):
    """Inline floating palette that appears above the tag pill."""

    color_selected = pyqtSignal(str)

    def __init__(self, current_color: str = None, parent=None):
        super().__init__(parent)
        global _active_popup, _focus_connected
        # Close any existing popup first
        if _active_popup is not None and _active_popup.isVisible():
            _active_popup.close()
        _active_popup = self

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(3)

        for color in TAG_COLORS:
            btn = ColorDot(color, is_current=(color == current_color))
            btn.color_selected.connect(self._on_color)
            layout.addWidget(btn)

        self.setStyleSheet("""
            QWidget {
                background: rgba(30, 30, 30, 230);
                border-radius: 5px;
                border: 1px solid rgba(255,255,255,20);
            }
        """)

        # Connect QApplication.focusChanged once
        if not _focus_connected:
            app = QApplication.instance()
            if app is not None:
                app.focusChanged.connect(_on_app_focus_changed)
            _focus_connected = True

    def _on_color(self, color: str):
        self.color_selected.emit(color)
        self.close()

    def popup_above(self, widget: QWidget):
        """Show popup positioned above the widget."""
        pos = widget.mapToGlobal(QPoint(0, -self.sizeHint().height() - 4))
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        global _active_popup
        if _active_popup is self:
            _active_popup = None
        super().closeEvent(event)
