import sys
from PyQt6.QtWidgets import QApplication
from src import __version__
from src.backend.icon import get_app_icon
from src.backend.paths import get_data_dir, migrate_legacy_data
from src.backend.state_manager import StateManager
from src.frontend.main_window import MainWindow
from src.frontend.theme import apply_theme_to_app, normalize_theme_id


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nudge")
    app.setApplicationDisplayName("Nudge")
    app.setApplicationVersion(__version__)
    app.setQuitOnLastWindowClosed(True)

    # Set the default window icon (used by every top-level widget /
    # dialog title bar). The taskbar also reads this, but Windows
    # sometimes needs a per-window setWindowIcon() — MainWindow does that.
    app.setWindowIcon(get_app_icon())

    # Resolve the per-user data directory and migrate any pre-AppData state
    # before any store tries to read or write a file.
    data_dir = get_data_dir()
    migrated = migrate_legacy_data()
    if migrated:
        print(f"[Nudge] Data directory: {data_dir} (migrated legacy files)")

    # Apply saved theme before any window is shown (avoids flash of wrong theme).
    boot_state = StateManager("appstate.json").load()
    apply_theme_to_app(
        app,
        normalize_theme_id(boot_state.get("theme")),
    )

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
