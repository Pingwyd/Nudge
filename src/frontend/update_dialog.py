from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
)

from src import __version__
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.theme import get_theme, normalize_theme_id
from src.constants import (
    UPDATE_INFO_DIALOG_DEFAULT,
    UPDATE_INFO_DIALOG_MIN,
    DOWNLOAD_DIALOG_DEFAULT,
    DOWNLOAD_DIALOG_MIN,
    DOWNLOAD_ERROR_MIN_SIZE,
    DOWNLOAD_ERROR_WIDTH,
    DOWNLOAD_ERROR_MAX_HEIGHT,
    DOWNLOAD_ERROR_HEIGHT_BASE,
    DOWNLOAD_ERROR_TEXT_MIN_H,
    PROGRESS_BAR_HEIGHT,
    PROGRESS_BAR_RADIUS,
    PROGRESS_CHUNK_RADIUS,
    PROGRESS_PCT_CAP,
    MARGIN_STANDARD,
    RADIUS_PANEL,
    RADIUS_BUTTON,
    SPACING_SM,
    SPACING_MD,
    SPACING_LG,
    FONT_SIZE_HINT,
    FONT_SIZE_LABEL_SM,
    FONT_SIZE_BODY,
    FONT_SIZE_TITLE_MD,
    FONT_SIZE_TITLE_LG,
    BTN_MIN_WIDTH_XL,
    MB_DIVISOR,
    DIALOG_BTN_ALPHA,
    DIALOG_EDIT_ALPHA,
    DIALOG_BTN_PAD_V,
    DIALOG_BTN_PAD_H,
    DIALOG_EDIT_PAD,
    DIALOG_BORDER_WIDTH,
)


def _changelog_to_html(text: str) -> str:
    if not text:
        return "<p>No release notes available.</p>"
    lines = text.split("\n")
    html_parts = [f'<div style="font-size:{FONT_SIZE_BODY}px; line-height:1.6;">']
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


class UpdateInfoDialog(GlassPanelDialog):
    def __init__(self, latest_version: str, changelog: str, download_url: str, parent=None):
        super().__init__(parent)
        self.latest_version = latest_version
        self.changelog = changelog
        self.download_url = download_url
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Update Available")
        self.resize(*UPDATE_INFO_DIALOG_DEFAULT)
        self.setMinimumSize(*UPDATE_INFO_DIALOG_MIN)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(*MARGIN_STANDARD)
        layout.setSpacing(SPACING_LG)

        title = QLabel(f"Update Available — Nudge v{self.latest_version}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(FONT_SIZE_TITLE_LG)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        current = QLabel(f"Current version: {__version__}")
        current.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cfont = current.font()
        cfont.setPointSize(FONT_SIZE_TITLE_MD)
        current.setFont(cfont)
        layout.addWidget(current)

        changelog_label = QLabel("What's new:")
        clfont = changelog_label.font()
        clfont.setPointSize(FONT_SIZE_TITLE_MD)
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
        nfont.setPointSize(FONT_SIZE_HINT)
        note.setFont(nfont)
        layout.addWidget(note)

        btn_row = QHBoxLayout()
        later_btn = QPushButton("Remind Me Later")
        later_btn.setObjectName("ghostButton")
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


class DownloadThread(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(bool, str, str, str)

    def __init__(
        self,
        download_url: str,
        version: str,
        asset_kind: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.download_url = download_url
        self.version = version
        self.asset_kind = asset_kind

    def run(self):
        from src.backend.updater import download_update
        import tempfile

        temp_dir = Path(tempfile.gettempdir()) / "Nudge_update"
        path, err = download_update(
            self.download_url,
            temp_dir,
            self.version,
            progress_callback=lambda dl, total: self.progress.emit(dl, total),
            asset_kind=self.asset_kind,
        )
        if path is not None:
            self.finished.emit(True, "", str(path), self.version)
        else:
            self.finished.emit(False, err, "", self.version)


class DownloadDialog(GlassPanelDialog):
    download_ready = pyqtSignal(str, str)

    def __init__(
        self,
        latest_version: str,
        download_url: str,
        asset_kind: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.latest_version = latest_version
        self.download_url = download_url
        self.asset_kind = asset_kind
        self._thread = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Downloading Update")
        self.resize(*DOWNLOAD_DIALOG_DEFAULT)
        self.setMinimumSize(*DOWNLOAD_DIALOG_MIN)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"Downloading Nudge v{self.latest_version}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(FONT_SIZE_TITLE_MD)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        self.status_label = QLabel("Preparing download...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        sfont = self.status_label.font()
        sfont.setPointSize(FONT_SIZE_HINT)
        self.status_label.setFont(sfont)
        layout.addWidget(self.status_label)

        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setVisible(False)
        self.error_text.setMinimumHeight(DOWNLOAD_ERROR_TEXT_MIN_H)
        efont = self.error_text.font()
        efont.setPointSize(FONT_SIZE_HINT)
        self.error_text.setFont(efont)
        layout.addWidget(self.error_text, stretch=1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(PROGRESS_BAR_HEIGHT)
        layout.addWidget(self.progress_bar)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("primaryButton")
        self.cancel_btn.setFixedWidth(BTN_MIN_WIDTH_XL)
        self.cancel_btn.clicked.connect(self._on_cancel)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._apply_theme()

    def start_download(self):
        self._thread = DownloadThread(
            self.download_url,
            self.latest_version,
            self.asset_kind,
            self,
        )
        self._thread.progress.connect(self._on_progress)
        self._thread.finished.connect(self._on_finished)
        self._thread.start()

    def _on_progress(self, downloaded: int, total: int):
        if total > 0:
            self.progress_bar.setRange(0, 100)
            pct = min(int(downloaded * 100 / total), PROGRESS_PCT_CAP)
            self.progress_bar.setValue(pct)
            mb_dl = downloaded / MB_DIVISOR
            mb_total = total / MB_DIVISOR
            self.status_label.setText(f"{mb_dl:.1f} MB / {mb_total:.1f} MB")
        else:
            mb_dl = downloaded / MB_DIVISOR
            self.progress_bar.setRange(0, 0)
            self.status_label.setText(f"Downloaded {mb_dl:.1f} MB\u2026")

    def _on_finished(self, success: bool, error_msg: str = "", path: str = "", version: str = ""):
        if not self.isVisible():
            return
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("Download complete!")
            self.download_ready.emit(path, version)
            self.close()
        else:
            self.cancel_btn.setText("Close")
            detail = error_msg or "Download failed. Please try again later."
            self.status_label.setText("Download failed")
            self.error_text.setPlainText(detail)
            self.error_text.setVisible(True)
            self.setMinimumSize(*DOWNLOAD_ERROR_MIN_SIZE)
            self.resize(DOWNLOAD_ERROR_WIDTH, min(DOWNLOAD_ERROR_MAX_HEIGHT, DOWNLOAD_ERROR_HEIGHT_BASE + self.error_text.document().size().height()))
            self.adjustSize()
            self.progress_bar.setValue(0)

    def _on_cancel(self):
        if self._thread and self._thread.isRunning():
            self._thread.terminate()
            self._thread.wait()
        self.close()

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

        self.bg_frame.setStyleSheet(f"""
            QWidget#glassPanel {{
                background: {bg};
                border-radius: {RADIUS_PANEL}px;
                border: {DIALOG_BORDER_WIDTH}px solid {border};
            }}
            QLabel {{
                color: {text};
                background: transparent;
            }}
            QProgressBar {{
                background: {muted};
                border: {DIALOG_BORDER_WIDTH}px solid {border};
                border-radius: {PROGRESS_BAR_RADIUS}px;
                text-align: center;
                color: {text};
            }}
            QProgressBar::chunk {{
                background: {accent};
                border-radius: {PROGRESS_CHUNK_RADIUS}px;
            }}
            QPushButton {{
                background: rgba(255,255,255,{DIALOG_BTN_ALPHA});
                color: {text};
                border: {DIALOG_BORDER_WIDTH}px solid {border};
                border-radius: {RADIUS_BUTTON}px;
                padding: {DIALOG_BTN_PAD_V}px {DIALOG_BTN_PAD_H}px;
                font-size: {FONT_SIZE_LABEL_SM}px;
            }}
            QPushButton:hover {{
                background: {hover};
            }}
            QTextEdit {{
                background: rgba(0,0,0,{DIALOG_EDIT_ALPHA});
                color: #ff6b6b;
                border: {DIALOG_BORDER_WIDTH}px solid {border};
                border-radius: {PROGRESS_BAR_RADIUS}px;
                padding: {DIALOG_EDIT_PAD}px;
            }}
        """)


class InstallReadyDialog(GlassPanelDialog):
    def __init__(self, latest_version: str, from_cache: bool = False, parent=None):
        super().__init__(parent)
        self.latest_version = latest_version
        self.from_cache = from_cache
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Update Ready")
        self.resize(*DOWNLOAD_DIALOG_DEFAULT)
        self.setMinimumSize(*DOWNLOAD_DIALOG_MIN)

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"Nudge v{self.latest_version} is ready to install")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title.font()
        font.setPointSize(FONT_SIZE_TITLE_MD)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        if self.from_cache:
            subtitle = QLabel("Previously downloaded — ready when you are.")
        else:
            subtitle = QLabel("The app will restart after installing.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        sfont = subtitle.font()
        sfont.setPointSize(FONT_SIZE_HINT)
        subtitle.setFont(sfont)
        layout.addWidget(subtitle)

        layout.addStretch()

        btn_row = QHBoxLayout()
        later_btn = QPushButton("Remind Me Later")
        later_btn.setObjectName("ghostButton")
        later_btn.clicked.connect(self.reject)
        btn_row.addWidget(later_btn)

        install_btn = QPushButton("Install Now")
        install_btn.setObjectName("primaryButton")
        ifont = install_btn.font()
        ifont.setBold(True)
        install_btn.setFont(ifont)
        install_btn.clicked.connect(self.accept)
        btn_row.addWidget(install_btn)

        layout.addLayout(btn_row)

        self._apply_theme()

    def _apply_theme(self):
        parent = self.parent()
        theme_id = normalize_theme_id(getattr(parent, "app_state", {}).get("theme", "dark")) if parent else "dark"
        theme = get_theme(theme_id)
        bg = theme["colors"].get("menu_bg", "rgba(30,30,30,240)")
        border = theme["colors"].get("border", "rgba(255,255,255,60)")
        text = theme["colors"].get("text", "#e0e0e0")
        hover = theme["colors"].get("hover", "rgba(255,255,255,20)")

        self.bg_frame.setStyleSheet(f"""
            QWidget#glassPanel {{
                background: {bg};
                border-radius: {RADIUS_PANEL}px;
                border: {DIALOG_BORDER_WIDTH}px solid {border};
            }}
            QLabel {{
                color: {text};
                background: transparent;
            }}
            QPushButton {{
                background: rgba(255,255,255,{DIALOG_BTN_ALPHA});
                color: {text};
                border: {DIALOG_BORDER_WIDTH}px solid {border};
                border-radius: {RADIUS_BUTTON}px;
                padding: {DIALOG_BTN_PAD_V}px {DIALOG_BTN_PAD_H}px;
                font-size: {FONT_SIZE_LABEL_SM}px;
            }}
            QPushButton:hover {{
                background: {hover};
            }}
            QPushButton#primaryButton {{
                background: {theme["colors"].get("accent", "#4fc3f7")};
                color: #000;
                border: none;
                font-weight: bold;
            }}
            QPushButton#primaryButton:hover {{
                background: {theme["colors"].get("accent_hover", "#81d4fa")};
            }}
        """)
