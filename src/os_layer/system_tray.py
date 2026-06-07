from __future__ import annotations
from typing import Callable, Optional
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal

class SystemTrayManager(QObject):
    show_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, app: QApplication, icon: QIcon, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._app = app
        self._tray = QSystemTrayIcon(icon, app)
        self._tray.setToolTip("Nudge Task Widget")

        menu = QMenu()
        show_action = QAction("Show", app)
        show_action.triggered.connect(self.show_requested.emit)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("Quit", app)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_requested.emit()

    def show_message(self, title: str, message: str, msecs: int = 3000):
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, msecs)

    def hide(self):
        self._tray.hide()

    def is_visible(self) -> bool:
        return self._tray.isVisible()
