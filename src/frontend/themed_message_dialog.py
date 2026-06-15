"""
Themed, frameless message box that matches the app's glass panel style.

Replaces QMessageBox so native dialogs pick up the app theme and behave
like the rest of the side panels (overlap-aware opacity).
"""
from __future__ import annotations

from typing import Optional, Sequence

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.backend.icon import get_app_icon
from src.frontend.theme import (
    get_theme,
    glass_overlap_stylesheet,
    normalize_theme_id,
    refresh_glass_shells,
)


class ThemedMessageDialog(QDialog):
    """Themed Yes/No/Ok-style dialog. Returns the index of the clicked button."""

    def __init__(
        self,
        parent: Optional[QWidget],
        title: str,
        message: str,
        buttons: Sequence[str] = ("OK",),
        default_index: int = 0,
        icon_kind: str = "info",
    ):
        super().__init__(parent)
        self._result_index = -1
        self._drag_pos = None
        self._init_ui(title, message, list(buttons), default_index, icon_kind)

    def _init_ui(self, title, message, buttons, default_index, icon_kind):
        self.setWindowTitle(title)
        self.setWindowIcon(get_app_icon())
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        initial_w, initial_h = 350, 150
        self.resize(initial_w, initial_h)

        self.bg_frame = QFrame(self)
        self.bg_frame.setObjectName("glassPanel")
        self.bg_frame.setGeometry(0, 0, 350, 150)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._title_label)

        self._msg_label = QLabel(message)
        self._msg_label.setWordWrap(True)
        self._msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._msg_label, 1)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.addStretch(1)
        self._buttons = []
        for i, label in enumerate(buttons):
            btn = QPushButton(label)
            btn.setObjectName("ghostButton")
            btn.setFixedHeight(28)
            btn.setMinimumWidth(70)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self._on_button_clicked(idx))
            self._buttons.append(btn)
            button_row.addWidget(btn)
        layout.addLayout(button_row)

        if 0 <= default_index < len(self._buttons):
            self._buttons[default_index].setDefault(True)
            self._buttons[default_index].setFocus()

        self.setMinimumWidth(360)
        self._size_to_content()
        self._update_overlap_opacity()

    def _size_to_content(self) -> None:
        m = self.bg_frame.layout().contentsMargins()
        sp = self.bg_frame.layout().spacing()

        # Measure the longest text line to pick a width that doesn't clip.
        longest = 0
        for label in (self._title_label, self._msg_label):
            fm = QFontMetrics(label.font())
            for line in label.text().split("\n"):
                longest = max(longest, fm.horizontalAdvance(line))
        available_w = max(320, longest + m.left() + m.right() + 40)
        self.resize(available_w, 160)

        text_w = available_w - m.left() - m.right()

        # Title height
        title_h = self._title_label.sizeHint().height()

        # Message height wrapped to text_w
        fm = QFontMetrics(self._msg_label.font())
        bounds = fm.boundingRect(0, 0, text_w, 10000, int(Qt.TextFlag.TextWordWrap), self._msg_label.text())

        # Buttons height
        btn_h = 32

        total_h = m.top() + title_h + sp + bounds.height() + 8 + sp + btn_h + m.bottom()
        self.resize(available_w, total_h)

    def resizeEvent(self, event):
        self.bg_frame.setGeometry(self.rect())
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
            theme_id = normalize_theme_id(parent.app_state.get("theme", "dark"))
            theme = get_theme(theme_id)
            self.bg_frame.setStyleSheet(glass_overlap_stylesheet(theme, radius=16))
        else:
            theme_id = normalize_theme_id(parent.app_state.get("theme", "dark"))
            refresh_glass_shells(self, theme_id)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            default = 0
            for i, btn in enumerate(self._buttons):
                if btn.isDefault():
                    default = i
                    break
            self._on_button_clicked(default)
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_button_clicked(self, index):
        self._result_index = index
        self.accept()

    def result_index(self) -> int:
        return self._result_index

    @staticmethod
    def question(
        parent: Optional[QWidget],
        title: str,
        message: str,
        yes_label: str = "Yes",
        no_label: str = "No",
        default_yes: bool = True,
    ) -> bool:
        buttons = [yes_label, no_label]
        default_index = 0 if default_yes else 1
        dialog = ThemedMessageDialog(parent, title, message, buttons, default_index, "question")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.result_index() == 0
        return False

    @staticmethod
    def warning(parent: Optional[QWidget], title: str, message: str) -> None:
        dialog = ThemedMessageDialog(parent, title, message, ["OK"], 0, "warning")
        dialog.exec()

    @staticmethod
    def information(parent: Optional[QWidget], title: str, message: str) -> None:
        from PyQt6.QtCore import QObject
        from PyQt6.QtWidgets import QApplication as _QApp

        dialog = ThemedMessageDialog(parent, title, message, ["OK"], 0, "info")
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        class _DismissOnOutsideClick(QObject):
            def eventFilter(self, obj, event):
                if event.type() == QEvent.Type.MouseButtonPress:
                    if not dialog.isVisible():
                        return False
                    click_pt = event.globalPosition().toPoint()
                    if not dialog.frameGeometry().contains(click_pt):
                        dialog.close()
                return False

        _filter = _DismissOnOutsideClick()
        qapp = _QApp.instance()
        qapp.installEventFilter(_filter)
        dialog.finished.connect(lambda: qapp.removeEventFilter(_filter) if qapp else None)
        dialog.show()
