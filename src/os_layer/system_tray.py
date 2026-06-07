from __future__ import annotations

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction, QCursor
from PyQt6.QtCore import QObject, pyqtSignal, QPoint, QRect

from src import __app_name__, __version__


class SystemTrayManager(QObject):
    show_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    update_requested = pyqtSignal()

    def __init__(self, app: QApplication, icon: QIcon, parent: QObject | None = None):
        super().__init__(parent)
        self._app = app
        self._tray = QSystemTrayIcon(icon, app)
        self._tray.setToolTip(f"{__app_name__} v{__version__}")
        self._menu: QMenu | None = None

        self._build_menu()
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    def _build_menu(self, theme: dict | None = None) -> None:
        if theme is None:
            from src.frontend.theme import get_theme, normalize_theme_id
            from src.backend.state_manager import StateManager
            sm = StateManager()
            theme = get_theme(normalize_theme_id(sm.state.get("theme", "dark")))

        bg = theme["colors"].get("menu_bg", "rgba(40,40,40,220)")
        fg = theme["colors"].get("text", "#ffffff")
        border = theme["colors"].get("menu_border", "rgba(255,255,255,50)")
        hover = theme["colors"].get("hover", "rgba(255,255,255,40)")
        sep = theme["colors"].get("chrome_separator", "rgba(255,255,255,25)")

        if self._menu is not None:
            self._menu.deleteLater()

        menu = QMenu()
        menu.setObjectName("trayMenu")
        menu.setStyleSheet(f"""
            QMenu#trayMenu {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 6px 0;
            }}
            QMenu#trayMenu::item {{
                padding: 7px 20px 7px 16px;
                color: {fg};
            }}
            QMenu#trayMenu::item:selected {{
                background: {hover};
            }}
            QMenu#trayMenu::separator {{
                height: 1px;
                background: {sep};
                margin: 4px 10px;
            }}
        """)

        ver = menu.addAction(f"{__app_name__} v{__version__}")
        ver.setEnabled(False)
        font = ver.font()
        font.setPointSize(10)
        font.setBold(True)
        ver.setFont(font)

        menu.addSeparator()

        show_action = menu.addAction("Show Window")
        show_action.triggered.connect(self.show_requested.emit)

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self.settings_requested.emit)

        menu.addSeparator()

        update_action = menu.addAction("Check for Updates")
        update_action.triggered.connect(self.update_requested.emit)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_requested.emit)

        self._menu = menu

    def restyle(self, theme: dict | None = None) -> None:
        self._build_menu(theme)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Context:
            if self._menu is not None:
                pos = QCursor.pos()
                screen = QApplication.screenAt(pos)
                if screen is not None:
                    geo = screen.availableGeometry()
                    menu_h = self._menu.sizeHint().height()
                    menu_w = self._menu.sizeHint().width()
                    x = pos.x()
                    y = geo.bottom() - menu_h - 4
                    if x + menu_w > geo.right():
                        x = geo.right() - menu_w - 4
                    if x < geo.left():
                        x = geo.left() + 4
                    self._menu.popup(QPoint(x, y))
                else:
                    self._menu.popup(pos)
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_requested.emit()

    def show_message(self, title: str, message: str, msecs: int = 3000) -> None:
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, msecs)

    def hide(self) -> None:
        self._tray.hide()

    def is_visible(self) -> bool:
        return self._tray.isVisible()
