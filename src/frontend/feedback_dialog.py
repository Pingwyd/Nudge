from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src import __version__
from src.backend.icon import get_app_icon
from src.frontend.theme import (
    get_theme,
    glass_overlap_stylesheet,
    normalize_theme_id,
    refresh_glass_shells,
)


class FeedbackDialog(QDialog):
    def __init__(self, parent: Optional[QWidget], state_snapshot: str):
        super().__init__(parent)
        self.state_snapshot = state_snapshot
        self._drag_pos = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Send Feedback")
        self.setWindowIcon(get_app_icon())
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        w, h = 560, 460
        self.resize(w, h)
        self.setMinimumSize(420, 380)

        self.bg_frame = QFrame(self)
        self.bg_frame.setObjectName("glassPanel")
        self.bg_frame.setGeometry(0, 0, w, h)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(12)

        # ── Title + subtitle ──
        title = QLabel("Send Feedback")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Tell me what's on your mind. The app state below helps me debug issues — "
            "nothing is sent until you click the button."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("opacity: 0.8;")
        layout.addWidget(subtitle)

        # ── Feedback input card (primary focus) ──
        input_card = QFrame()
        input_card.setObjectName("nestedPanel")
        input_card_layout = QVBoxLayout(input_card)
        input_card_layout.setContentsMargins(12, 10, 12, 12)
        input_card_layout.setSpacing(6)

        input_header = QHBoxLayout()
        input_header.setSpacing(8)
        input_title = QLabel("Your feedback")
        input_title.setStyleSheet("font-weight: 600;")
        input_header.addWidget(input_title)
        input_header.addStretch()
        char_count = QLabel("0")
        char_count.setStyleSheet("opacity: 0.6;")
        self._char_count = char_count
        input_header.addWidget(char_count)
        input_card_layout.addLayout(input_header)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("What's something you'd like changed or improved?")
        self.input_edit.setMinimumHeight(110)
        self.input_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.input_edit.textChanged.connect(self._update_char_count)
        input_card_layout.addWidget(self.input_edit, 1)

        layout.addWidget(input_card, 1)

        # ── Snapshot section (collapsed by default) ──
        snapshot_header_row = QHBoxLayout()
        snapshot_header_row.setSpacing(8)
        self.snapshot_toggle = QPushButton("▸  App state snapshot")
        self.snapshot_toggle.setObjectName("ghostButton")
        self.snapshot_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.snapshot_toggle.setStyleSheet(
            "QPushButton#ghostButton { text-align: left; padding: 4px 8px; font-weight: 600; }"
        )
        self.snapshot_toggle.clicked.connect(self._toggle_snapshot)
        snapshot_header_row.addWidget(self.snapshot_toggle)
        snapshot_header_row.addStretch()

        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("ghostButton")
        copy_btn.setFixedHeight(26)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_snapshot)
        self._copy_btn = copy_btn
        snapshot_header_row.addWidget(copy_btn)

        layout.addLayout(snapshot_header_row)

        self.snapshot_card = QFrame()
        self.snapshot_card.setObjectName("nestedPanel")
        snapshot_card_layout = QVBoxLayout(self.snapshot_card)
        snapshot_card_layout.setContentsMargins(10, 8, 10, 8)
        snapshot_card_layout.setSpacing(0)

        self.snapshot_edit = QTextEdit()
        self.snapshot_edit.setReadOnly(True)
        self.snapshot_edit.setPlainText(self.state_snapshot)
        self.snapshot_edit.setStyleSheet(
            "QTextEdit { font-family: monospace; background: transparent; border: none; }"
        )
        self.snapshot_edit.setFixedHeight(140)
        snapshot_card_layout.addWidget(self.snapshot_edit)

        self.snapshot_card.setVisible(False)
        layout.addWidget(self.snapshot_card)

        # ── Footer note ──
        footer = QLabel(
            "A pre-filled email to nudgefeedback@gmail.com will open. "
            "The full text is also copied to your clipboard as a backup."
        )
        footer.setWordWrap(True)
        footer.setStyleSheet("opacity: 0.7;")
        layout.addWidget(footer)

        # ── Action buttons ──
        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.addStretch(1)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("ghostButton")
        self.cancel_btn.setFixedSize(110, 32)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_btn)

        self.open_btn = QPushButton("Open Gmail")
        self.open_btn.setObjectName("primaryButton")
        self.open_btn.setFixedSize(110, 32)
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.setDefault(True)
        self.open_btn.clicked.connect(self._send_feedback)
        button_row.addWidget(self.open_btn)

        layout.addLayout(button_row)

        self._update_overlap_opacity()
        QTimer.singleShot(0, self.input_edit.setFocus)

    def _update_char_count(self) -> None:
        text = self.input_edit.toPlainText()
        self._char_count.setText(str(len(text)))

    def _toggle_snapshot(self) -> None:
        visible = not self.snapshot_card.isVisible()
        self.snapshot_card.setVisible(visible)
        arrow = "▾" if visible else "▸"
        current = self.snapshot_toggle.text()
        if current[:1] in ("▸", "▾"):
            self.snapshot_toggle.setText(arrow + current[1:])
        else:
            self.snapshot_toggle.setText(arrow + "  " + current)

    def _copy_snapshot(self) -> None:
        QApplication.clipboard().setText(self.state_snapshot)
        original = self._copy_btn.text()
        self._copy_btn.setText("Copied!")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1200, lambda: self._copy_btn.setText(original))

    def _send_feedback(self) -> None:
        from urllib.parse import quote
        from src.os_layer.platform_utils import open_url

        text = self.feedback_text()
        if not text:
            return
        subject = f"Nudge Feedback v{__version__}"
        gmail_uri = (
            f"https://mail.google.com/mail/u/0/?view=cm&fs=1"
            f"&to=nudgefeedback@gmail.com"
            f"&su={quote(subject)}"
            f"&body={quote(text)}"
        )
        opened = open_url(gmail_uri)
        if opened:
            QApplication.clipboard().setText(text)
        self.accept()

    def feedback_text(self) -> str:
        return self.input_edit.toPlainText().strip()

    def resizeEvent(self, event):
        self.bg_frame.setGeometry(self.rect())
        super().resizeEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self._update_overlap_opacity()

    def _update_overlap_opacity(self):
        parent = self.parent()
        if parent is None:
            return
        if isinstance(parent, QDialog):
            parent = parent.parent()
        if parent is None:
            return
        overlap = self.frameGeometry().intersects(parent.frameGeometry())
        theme_id = normalize_theme_id(getattr(parent, "app_state", {}).get("theme", "dark"))
        if overlap:
            theme = get_theme(theme_id)
            self.bg_frame.setStyleSheet(glass_overlap_stylesheet(theme, radius=16))
        else:
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            event.accept()
            return
        super().keyPressEvent(event)
