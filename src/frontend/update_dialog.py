from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src import __version__
from src.frontend.theme import get_theme, normalize_theme_id, refresh_glass_shells


def _changelog_to_html(text: str) -> str:
    """Convert plain-text changelog (emoji headers + bullet items) to styled HTML."""
    if not text:
        return "<p>No release notes available.</p>"
    lines = text.split("\n")
    html_parts = ['<div style="font-size:13px; line-height:1.6;">']
    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_parts.append("<br>")
        elif stripped.startswith("•") or stripped.startswith("-"):
            html_parts.append(f'<li style="margin:2px 0;">{stripped[1:].strip()}</li>')
        else:
            html_parts.append(f'<p style="margin:8px 0 4px 0; font-weight:bold;">{stripped}</p>')
    html_parts.append("</div>")
    return "".join(html_parts)


class UpdateInfoDialog(QDialog):
    def __init__(self, latest_version: str, changelog: str, download_url: str, parent=None):
        super().__init__(parent)
        self.latest_version = latest_version
        self.changelog = changelog
        self.download_url = download_url
        self._drag_pos = None
        self.frame = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Update Available")
        self.resize(420, 480)
        self.setMinimumSize(320, 360)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.frame = QFrame(self)
        self.frame.setObjectName("glassPanel")
        self.frame.setGeometry(0, 0, 420, 480)

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel(f"Update Available — Nudge v{self.latest_version}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        current = QLabel(f"Current version: {__version__}")
        current.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cfont = current.font()
        cfont.setPointSize(12)
        current.setFont(cfont)
        layout.addWidget(current)

        changelog_label = QLabel("What's new:")
        clfont = changelog_label.font()
        clfont.setPointSize(14)
        clfont.setBold(True)
        changelog_label.setFont(clfont)
        layout.addWidget(changelog_label)

        self.changelog_browser = QTextBrowser()
        self.changelog_browser.setOpenExternalLinks(False)
        self.changelog_browser.setHtml(_changelog_to_html(self.changelog or "(No changelog available)"))
        self.changelog_browser.setStyleSheet("QTextBrowser { border: none; background: transparent; }")
        layout.addWidget(self.changelog_browser, stretch=1)

        note = QLabel("The app will restart after installing.")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nfont = note.font()
        nfont.setPointSize(10)
        note.setFont(nfont)
        layout.addWidget(note)

        btn_row = QHBoxLayout()
        later_btn = QPushButton("Remind Me Later")
        later_btn.setObjectName("primaryButton")
        later_btn.clicked.connect(self.reject)
        btn_row.addWidget(later_btn)

        install_btn = QPushButton("Download && Install")
        install_btn.setObjectName("primaryButton")
        ifont = install_btn.font()
        ifont.setBold(True)
        install_btn.setFont(ifont)
        install_btn.clicked.connect(self.accept)
        btn_row.addWidget(install_btn)

        layout.addLayout(btn_row)

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

    def resizeEvent(self, event):
        if self.frame is not None:
            self.frame.setGeometry(self.rect())
        super().resizeEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self._update_overlap_opacity()

    def _update_overlap_opacity(self):
        parent = self.parent()
        if parent is None:
            return
        theme_id = normalize_theme_id(getattr(parent, "app_state", {}).get("theme", "dark"))
        theme = get_theme(theme_id)
        overlap = self.frameGeometry().intersects(parent.frameGeometry()) if hasattr(parent, "frameGeometry") else False
        if overlap:
            solid = "rgba(248, 248, 250, 255)" if theme_id == "light" else "rgba(18, 18, 18, 255)"
            self.frame.setStyleSheet(f"""
                QWidget#glassPanel {{
                    background: {solid};
                    border-radius: 20px;
                    border: 1px solid {theme["colors"].get("border", "rgba(255,255,255,60)")};
                }}
            """)
        else:
            refresh_glass_shells(self, theme_id)


class DownloadThread(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(bool, str)

    def __init__(self, download_url: str, version: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.version = version

    def run(self):
        from src.backend.updater import download_update
        from pathlib import Path
        import tempfile

        temp_dir = Path(tempfile.gettempdir()) / "Nudge_update"
        path, err = download_update(
            self.download_url, temp_dir, self.version,
            progress_callback=lambda dl, total: self.progress.emit(dl, total),
        )
        self.finished.emit(path is not None, err)


class DownloadDialog(QDialog):
    def __init__(self, latest_version: str, download_url: str, parent=None):
        super().__init__(parent)
        self.latest_version = latest_version
        self.download_url = download_url
        self._drag_pos = None
        self.frame = None
        self._thread = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Downloading Update")
        self.resize(380, 180)
        self.setMinimumSize(300, 160)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.frame = QFrame(self)
        self.frame.setObjectName("glassPanel")
        self.frame.setGeometry(0, 0, 380, 180)

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"Downloading Nudge v{self.latest_version}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        self.status_label = QLabel("Preparing download...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        sfont = self.status_label.font()
        sfont.setPointSize(10)
        self.status_label.setFont(sfont)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(22)
        layout.addWidget(self.progress_bar)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("primaryButton")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._update_overlap_opacity()
        self._apply_theme()

    def start_download(self):
        self._thread = DownloadThread(self.download_url, self.latest_version, self)
        self._thread.progress.connect(self._on_progress)
        self._thread.finished.connect(self._on_finished)
        self._thread.start()

    def _on_progress(self, downloaded: int, total: int):
        if total > 0:
            pct = int(downloaded * 100 / total)
            self.progress_bar.setValue(pct)
            mb_dl = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_label.setText(f"{mb_dl:.1f} MB / {mb_total:.1f} MB")
        else:
            pct = int(downloaded / 1024) % 100  # animate bar from downloaded KB
            self.progress_bar.setValue(min(pct, 99))
            mb_dl = downloaded / (1024 * 1024)
            self.status_label.setText(f"{mb_dl:.1f} MB downloaded")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

    def _on_finished(self, success: bool, error_msg: str = ""):
        if success:
            from pathlib import Path
            import tempfile, sys
            self.progress_bar.setValue(100)
            if getattr(sys, "frozen", False):
                self.cancel_btn.setEnabled(False)
                self.status_label.setText("Download complete! Installing...")
                from src.backend.updater import _install_update, _PLATFORM_EXT
                temp_dir = Path(tempfile.gettempdir()) / "Nudge_update"
                asset_name = f"Nudge_{self.latest_version}{_PLATFORM_EXT}"
                downloaded = temp_dir / asset_name
                current_exe = Path(sys.executable)
                _install_update(downloaded, current_exe)
                self.accept()
                from PyQt6.QtWidgets import QApplication
                from src.frontend.main_window import MainWindow
                for w in QApplication.topLevelWindows():
                    if isinstance(w, MainWindow):
                        w._skip_close_confirm = True
                        w._force_quit = True
                        w.close()
                        break
            else:
                self.status_label.setText("Downloaded (dev mode)")
                self.cancel_btn.setText("Close")
        else:
            self.cancel_btn.setText("Close")
            detail = error_msg or "Download failed. Please try again later."
            self.status_label.setText(detail)
            self.progress_bar.setValue(0)
            self.adjustSize()

    def _on_cancel(self):
        if self._thread and self._thread.isRunning():
            self._thread.terminate()
            self._thread.wait()
        self.reject()

    def _apply_theme(self):
        parent = self.parent()
        theme_id = normalize_theme_id(getattr(parent, "app_state", {}).get("theme", "dark")) if parent else "dark"
        theme = get_theme(theme_id)
        bg = theme["colors"].get("menu_bg", "rgba(30,30,30,240)")
        border = theme["colors"].get("border", "rgba(255,255,255,60)")
        text = theme["colors"].get("text", "#e0e0e0")
        muted = theme["colors"].get("muted", "#888888")
        accent = theme["colors"].get("accent", "#4fc3f7")
        hover = theme["colors"].get("hover", "rgba(255,255,255,20)")

        self.frame.setStyleSheet(f"""
            QWidget#glassPanel {{
                background: {bg};
                border-radius: 20px;
                border: 1px solid {border};
            }}
            QLabel {{
                color: {text};
                background: transparent;
            }}
            QProgressBar {{
                background: rgba(255,255,255,15);
                border: 1px solid {border};
                border-radius: 6px;
                text-align: center;
                color: {text};
            }}
            QProgressBar::chunk {{
                background: {accent};
                border-radius: 5px;
            }}
            QPushButton {{
                background: rgba(255,255,255,15);
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 6px 16px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {hover};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def resizeEvent(self, event):
        if self.frame is not None:
            self.frame.setGeometry(self.rect())
        super().resizeEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        self._update_overlap_opacity()

    def _update_overlap_opacity(self):
        parent = self.parent()
        if parent is None:
            return
        theme_id = normalize_theme_id(getattr(parent, "app_state", {}).get("theme", "dark"))
        theme = get_theme(theme_id)
        overlap = self.frameGeometry().intersects(parent.frameGeometry()) if hasattr(parent, "frameGeometry") else False
        if overlap:
            solid = "rgba(248, 248, 250, 255)" if theme_id == "light" else "rgba(18, 18, 18, 255)"
            self.frame.setStyleSheet(f"""
                QWidget#glassPanel {{
                    background: {solid};
                    border-radius: 20px;
                    border: 1px solid {theme["colors"].get("border", "rgba(255,255,255,60)")};
                }}
            """)
        else:
            refresh_glass_shells(self, theme_id)
