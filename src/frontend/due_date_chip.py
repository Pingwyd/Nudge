"""DueDateChip widget for displaying task due dates."""

from datetime import datetime, date
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget
from src.frontend.theme import _c, get_theme, normalize_theme_id


class DueDateChip(QWidget):
    """Compact chip showing due date with color coding."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._due_date = None
        self._theme_id = "dark"
        
        self.setFixedHeight(22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to set due date")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 1, 4, 1)
        layout.setSpacing(0)
        
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)
        
        self.hide()

    def set_due_date(self, due_date_str: str | None, theme_id: str = "dark"):
        """Set the due date to display."""
        self._due_date = due_date_str
        self._theme_id = normalize_theme_id(theme_id)

        if not due_date_str:
            self.hide()
            return

        self._update_display()
        self.show()

    def update_theme(self, theme_id: str | None = None) -> None:
        """Re-apply label colors after a global theme change."""
        if theme_id is not None:
            self._theme_id = normalize_theme_id(theme_id)
        if self._due_date:
            self._update_display()

    def _update_display(self):
        """Update the label text and color based on due date."""
        if not self._due_date:
            return
        
        try:
            due = datetime.strptime(self._due_date, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            self.hide()
            return
        
        today = date.today()
        tomorrow = today + __import__('datetime').timedelta(days=1)
        
        theme = get_theme(self._theme_id)
        text_color = _c(theme, "text")
        chip_css = (
            f"color: {text_color}; font-size: 11px; "
            "background: transparent; border: none;"
        )

        if due == today:
            self._label.setText("Due today")
            self._label.setStyleSheet(chip_css)
        elif due == tomorrow:
            self._label.setText("Due tomorrow")
            self._label.setStyleSheet(chip_css)
        elif due < today:
            days_overdue = (today - due).days
            self._label.setText(f"Overdue ({days_overdue}d)")
            self._label.setStyleSheet(
                "color: #ff9800; font-size: 11px; background: transparent; border: none;"
            )
        else:
            # Future date - show "Tue 24 Jun" format
            self._label.setText(due.strftime("%a %d %b"))
            self._label.setStyleSheet(chip_css)
        
        self.setToolTip(self._get_full_date_tooltip(due))

    def _get_full_date_tooltip(self, due: date) -> str:
        """Get full date string for tooltip."""
        return due.strftime("%A, %B %d, %Y")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
