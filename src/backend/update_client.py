"""Qt-based HTTP client for update check and download."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtCore import QObject, QTimer, QUrl, pyqtSignal
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from src import __version__

log = logging.getLogger(__name__)


class UpdateHttpError(Exception):
    """Raised when a Qt network request fails."""


def github_headers() -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"Nudge/{__version__}",
    }


def _apply_headers(request: QNetworkRequest, headers: dict[str, str]) -> None:
    for key, value in headers.items():
        request.setRawHeader(key.encode(), value.encode())


class UpdateClient(QObject):
    """Async update check and download via QNetworkAccessManager."""

    check_finished = pyqtSignal(object)
    download_progress = pyqtSignal(int, int)
    download_finished = pyqtSignal(bool, str, str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._download_reply: QNetworkReply | None = None
        self._download_file = None
        self._download_dest: Path | None = None
        self._download_version = ""
        self._pending_version = ""
        self._check_mode = "api"

    def start_check(self, current_version: str, check_url: str | None = None) -> None:
        from src.backend.updater import GITHUB_RELEASES_LATEST_PAGE, normalize_update_check_url

        self._pending_version = current_version
        self._begin_check(normalize_update_check_url(check_url), mode="api")

    def _begin_check(self, url: str, mode: str) -> None:
        self._check_mode = mode
        request = QNetworkRequest(QUrl(url))
        _apply_headers(request, github_headers())
        reply = self._nam.get(request)
        reply.finished.connect(lambda: self._on_check_finished(reply))

    def _on_check_finished(self, reply: QNetworkReply) -> None:
        from src.backend.updater import (
            GITHUB_RELEASES_LATEST_PAGE,
            UpdateCheckResult,
            check_for_update_from_body,
            check_for_update_from_redirect,
        )

        current_version = self._pending_version
        mode = self._check_mode
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                err = reply.errorString()
                if mode == "api" and "403" in err:
                    reply.deleteLater()
                    self._begin_check(GITHUB_RELEASES_LATEST_PAGE, mode="redirect")
                    return
                result = UpdateCheckResult(error=err)
            elif mode == "redirect":
                result = check_for_update_from_redirect(
                    reply.url().toString(),
                    current_version,
                )
            else:
                body = bytes(reply.readAll())
                result = check_for_update_from_body(body, current_version)
        finally:
            reply.deleteLater()
        self.check_finished.emit(result)

    def start_download(
        self,
        download_url: str,
        dest_path: Path,
        version: str,
    ) -> None:
        self.cancel_download()
        self._download_dest = dest_path
        self._download_version = version
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        self._download_file = open(dest_path, "wb")

        request = QNetworkRequest(QUrl(download_url))
        _apply_headers(request, github_headers())
        reply = self._nam.get(request)
        self._download_reply = reply
        reply.downloadProgress.connect(self._on_download_progress)
        reply.readyRead.connect(lambda: self._on_download_ready_read(reply))
        reply.finished.connect(lambda: self._on_download_finished(reply))

    def cancel_download(self) -> None:
        if self._download_reply is not None:
            self._download_reply.abort()
            self._download_reply.deleteLater()
            self._download_reply = None
        self._close_download_file()
        self._download_dest = None
        self._download_version = ""

    def _on_download_progress(self, received: int, total: int) -> None:
        self.download_progress.emit(received, total)

    def _on_download_ready_read(self, reply: QNetworkReply) -> None:
        if self._download_file is not None:
            self._download_file.write(reply.readAll())

    def _on_download_finished(self, reply: QNetworkReply) -> None:
        version = self._download_version
        dest = self._download_dest
        self._download_reply = None
        self._close_download_file()

        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                err = reply.errorString()
                if dest and dest.exists():
                    dest.unlink(missing_ok=True)
                self.download_finished.emit(False, err, "", version)
                return
            if dest is None or not dest.exists() or dest.stat().st_size == 0:
                if dest and dest.exists():
                    dest.unlink(missing_ok=True)
                self.download_finished.emit(False, "Download produced no data", "", version)
                return
            self.download_finished.emit(True, "", str(dest), version)
        finally:
            reply.deleteLater()
            self._download_dest = None
            self._download_version = ""

    def _close_download_file(self) -> None:
        if self._download_file is not None:
            try:
                self._download_file.close()
            except OSError:
                pass
            self._download_file = None


def fetch_bytes(
    url: str,
    headers: dict[str, str] | None = None,
    timeout_ms: int = 10000,
) -> bytes:
    """Blocking GET for scripts/tests. Requires a running QApplication."""
    from PyQt6.QtCore import QEventLoop
    from PyQt6.QtWidgets import QApplication

    if QApplication.instance() is None:
        raise UpdateHttpError("QApplication required for update network requests")

    nam = QNetworkAccessManager()
    request = QNetworkRequest(QUrl(url))
    _apply_headers(request, headers or github_headers())

    loop = QEventLoop()
    result: dict[str, bytes | str | None] = {"data": None, "error": None}
    reply = nam.get(request)

    def _on_finished() -> None:
        if reply.error() != QNetworkReply.NetworkError.NoError:
            result["error"] = reply.errorString()
        else:
            result["data"] = bytes(reply.readAll())
        loop.quit()

    reply.finished.connect(_on_finished)

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(
        lambda: (
            reply.abort(),
            result.__setitem__("error", "Request timed out"),
            loop.quit(),
        )
    )
    timer.start(timeout_ms)
    loop.exec()
    timer.stop()
    reply.deleteLater()

    if result["error"]:
        raise UpdateHttpError(str(result["error"]))
    data = result["data"]
    if not data:
        raise UpdateHttpError("Empty response")
    return data


def fetch_final_url(
    url: str,
    headers: dict[str, str] | None = None,
    timeout_ms: int = 10000,
) -> str:
    """Blocking GET that returns the final URL after redirects."""
    from PyQt6.QtCore import QEventLoop
    from PyQt6.QtWidgets import QApplication

    if QApplication.instance() is None:
        raise UpdateHttpError("QApplication required for update network requests")

    nam = QNetworkAccessManager()
    request = QNetworkRequest(QUrl(url))
    _apply_headers(request, headers or github_headers())

    loop = QEventLoop()
    result: dict[str, str | None] = {"url": None, "error": None}
    reply = nam.get(request)

    def _on_finished() -> None:
        if reply.error() != QNetworkReply.NetworkError.NoError:
            result["error"] = reply.errorString()
        else:
            result["url"] = reply.url().toString()
        loop.quit()

    reply.finished.connect(_on_finished)

    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(
        lambda: (
            reply.abort(),
            result.__setitem__("error", "Request timed out"),
            loop.quit(),
        )
    )
    timer.start(timeout_ms)
    loop.exec()
    timer.stop()
    reply.deleteLater()

    if result["error"]:
        raise UpdateHttpError(str(result["error"]))
    final_url = result["url"]
    if not final_url:
        raise UpdateHttpError("Empty redirect URL")
    return final_url


def download_file(
    url: str,
    dest_path: Path,
    progress_callback: Callable[[int, int], None] | None = None,
    headers: dict[str, str] | None = None,
    timeout_ms: int = 120000,
) -> None:
    """Blocking download for worker threads. Requires a running QApplication."""
    from PyQt6.QtCore import QEventLoop
    from PyQt6.QtWidgets import QApplication

    if QApplication.instance() is None:
        raise UpdateHttpError("QApplication required for update network requests")

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    nam = QNetworkAccessManager()
    request = QNetworkRequest(QUrl(url))
    _apply_headers(request, headers or github_headers())

    loop = QEventLoop()
    error_msg: list[str] = []
    reply = nam.get(request)

    with open(dest_path, "wb") as out_file:
        def _on_ready_read() -> None:
            out_file.write(reply.readAll())

        def _on_progress(received: int, total: int) -> None:
            if progress_callback:
                progress_callback(received, total)

        def _on_finished() -> None:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                error_msg.append(reply.errorString())
            loop.quit()

        reply.readyRead.connect(_on_ready_read)
        reply.downloadProgress.connect(_on_progress)
        reply.finished.connect(_on_finished)

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(
            lambda: (
                reply.abort(),
                error_msg.append("Download timed out"),
                loop.quit(),
            )
        )
        timer.start(timeout_ms)
        loop.exec()
        timer.stop()

    reply.deleteLater()

    if error_msg:
        dest_path.unlink(missing_ok=True)
        raise UpdateHttpError(error_msg[0])
    if not dest_path.exists() or dest_path.stat().st_size == 0:
        dest_path.unlink(missing_ok=True)
        raise UpdateHttpError("Download produced no data")
