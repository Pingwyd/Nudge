"""Runtime verification for Phase 7.1."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

app = QApplication(sys.argv)

# Test 1: Create MainWindow
from src.frontend.main_window import MainWindow
w = MainWindow()
assert w is not None
print("PASS: MainWindow created")

# Test 2: Basic state exists
state = w.state_manager.state
assert "taskTextSize" in state
assert "theme" in state
assert "groupsEnabled" in state
print(f"PASS: State loaded, theme={state['theme']}")

# Test 3: Toggle visibility
w.show()
w.hide()
print("PASS: show/hide works")

# Test 4: Import task group section
from src.frontend.task_group_section import TaskGroupSection
print("PASS: TaskGroupSection importable")

# Test 5: Check theme module
from src.frontend.theme import build_application_stylesheet, get_theme, DARK_THEME, LIGHT_THEME
theme = get_theme("dark")
qss = build_application_stylesheet(theme)
assert len(qss) > 100
print("PASS: theme module works")

# Test 6: Responsive text
from src.frontend.responsive_text import min_text_column_width
w100 = min_text_column_width(100)
w500 = min_text_column_width(500)
assert w100 >= 100, f"min width too small: {w100}"
assert w500 >= 100, f"min width too small: {w500}"
print(f"PASS: responsive_text (100px->{w100}, 500px->{w500})")

# Test 7: System tray
from src.os_layer.system_tray import SystemTrayManager
print("PASS: SystemTrayManager importable")

# Test 8: Support dialog
from src.frontend.support_dialog import SupportDialog
dlg = SupportDialog(w)
dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
dlg.exec()
print("PASS: SupportDialog opens")

# Test 9: WhatsNew dialog
from src.frontend.whats_new_dialog import WhatsNewDialog
dlg2 = WhatsNewDialog("Test changelog", w)
dlg2.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
dlg2.exec()
print("PASS: WhatsNewDialog opens")

# Test 10: Export dialog
from src.frontend.export_dialog import ExportDialog
print("PASS: ExportDialog importable")

# Cleanup
w.close()
app.quit()
print(f"\nALL PASS: 10/10 runtime checks")
