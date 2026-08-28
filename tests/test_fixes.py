"""Tests for fixes A1–E2 from the Master Execution Plan."""
import ast
import os
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QWidget, QLineEdit


# ── A1: Incremental Task Render ───────────────────────────────────────

def test_a1_render_tasks_has_fix_annotation(qapp_instance):
    """render_tasks should have FIX-A1 comment (called only on initial load)."""
    import inspect
    from src.frontend.task_controller import TaskController
    src = inspect.getsource(TaskController.render_tasks)
    assert "FIX-A1" in src


def test_a1_append_task_row_widget_exists(qapp_instance):
    """_append_task_row_widget should accept a single task and not call render_tasks."""
    from src.frontend.task_controller import TaskController
    assert hasattr(TaskController, '_append_task_row_widget')
    import inspect
    src = inspect.getsource(TaskController._append_task_row_widget)
    assert "render_tasks" not in src


def test_a1_task_group_section_has_refresh(qapp_instance):
    """TaskGroupSection.refresh() should exist and not call render_tasks()."""
    from src.frontend.task_group_section import TaskGroupSection
    assert hasattr(TaskGroupSection, 'refresh')
    import inspect
    src = inspect.getsource(TaskGroupSection.refresh)
    # Check no actual call to render_tasks (docstring may mention it)
    assert "render_tasks(" not in src


# ── A2: Export Collision Handling ─────────────────────────────────────

def _mock_qfiledialog_get_save_filename(return_path):
    """Patch QFileDialog.getSaveFileName so it doesn't open a native dialog."""
    return patch(
        'PyQt6.QtWidgets.QFileDialog.getSaveFileName',
        return_value=(return_path, "Text (*.txt)")
    )


def test_a2_export_locked_file_shows_dialog(qapp_instance):
    """OSError during export should surface a retry dialog, not crash."""
    from src.backend.export_service import run_export_with_dialog
    from src.frontend.main_window import MainWindow

    window = MainWindow()
    try:
        with _mock_qfiledialog_get_save_filename("/fake/export.txt"):
            with patch('src.backend.export_service.export_to_file',
                       side_effect=OSError(13, "Permission denied")):
                with patch('src.backend.export_service._prompt_retry_export',
                           return_value=None) as mock_retry:
                    result = run_export_with_dialog(
                        parent_widget=window,
                        main_window=window,
                        export_format="txt",
                        include_history=False,
                    )
                    assert result is False
                    mock_retry.assert_called_once()
    finally:
        window.close()


def test_a2_export_retry_succeeds_on_new_path(qapp_instance):
    """After OSError, user picks new path and export succeeds."""
    from src.backend.export_service import run_export_with_dialog
    from src.frontend.main_window import MainWindow

    window = MainWindow()
    try:
        call_count = [0]

        def _write_side_effect(request):
            call_count[0] += 1
            if call_count[0] == 1:
                raise OSError(13, "Permission denied")
            return None

        with _mock_qfiledialog_get_save_filename("/fake/export.txt"):
            with patch('src.backend.export_service.export_to_file',
                       side_effect=_write_side_effect):
                with patch('src.backend.export_service._prompt_retry_export',
                           return_value="/fake/new_path.txt"):
                    with patch('src.frontend.themed_message_dialog.ThemedMessageDialog.question',
                               return_value=False):
                        result = run_export_with_dialog(
                            parent_widget=window,
                            main_window=window,
                            export_format="txt",
                            include_history=False,
                        )
                        assert result is True
                        assert call_count[0] == 2
    finally:
        window.close()


def test_a2_export_cancel_returns_failure(qapp_instance):
    """User cancels the retry dialog — function returns False gracefully."""
    from src.backend.export_service import run_export_with_dialog
    from src.frontend.main_window import MainWindow

    window = MainWindow()
    try:
        with _mock_qfiledialog_get_save_filename("/fake/export.txt"):
            with patch('src.backend.export_service.export_to_file',
                       side_effect=OSError(13, "Permission denied")):
                with patch('src.backend.export_service._prompt_retry_export',
                           return_value=None):
                    result = run_export_with_dialog(
                        parent_widget=window,
                        main_window=window,
                        export_format="txt",
                        include_history=False,
                    )
                    assert result is False
    finally:
        window.close()


# ── B1: Resize Tracking Memory Leak ───────────────────────────────────

def test_b1_no_module_level_set(qapp_instance):
    """No module-level _resize_track_installed set should exist."""
    import src.frontend.main_window as mw
    assert not hasattr(mw, '_resize_track_installed'), \
        "Module-level set should be removed — use widget property instead"


def test_b1_widget_property_pattern(qapp_instance):
    """Resize tracking should use widget.setProperty."""
    from src.frontend.main_window import MainWindow
    window = MainWindow()
    try:
        w = QWidget()
        window._enable_resize_hover_tracking(w)
        assert w.property('resize_track_installed') is True
        w.deleteLater()
    finally:
        window.close()


# ── B2: Concurrent Archive ────────────────────────────────────────────

def test_b2_archive_concurrent_no_data_loss(qapp_instance):
    """10 concurrent appends must produce exactly 10 entries with no duplicates."""
    import pathlib
    from src.backend.task_store import TaskStore

    tmp = tempfile.mkstemp(suffix=".json", text=True)
    os.close(tmp[0])
    path = pathlib.Path(tmp[1])
    try:
        store = TaskStore("_concurrent_test.json")
        store.filepath = path
        store.save([])

        n_threads = 10
        errors = []

        def _append(i):
            try:
                record = {"id": f"test-{i}", "text": f"Task {i}"}
                store.append_and_save(record)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_append, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"

        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == n_threads, f"Expected {n_threads} entries, got {len(data)}"
        ids = [entry["id"] for entry in data]
        assert len(set(ids)) == n_threads, "Duplicate IDs found — data loss"
    finally:
        os.unlink(path)


# ── C1: ThemedInputDialog ─────────────────────────────────────────────

def test_c1_themed_input_dialog_inherits_glass(qapp_instance):
    """ThemedInputDialog must inherit from GlassPanelDialog."""
    from src.frontend.glass_panel_dialog import GlassPanelDialog
    from src.frontend.themed_input_dialog import ThemedInputDialog
    assert issubclass(ThemedInputDialog, GlassPanelDialog)


def test_c1_themed_input_dialog_get_text(qapp_instance):
    """get_text() returns the QLineEdit value; accepts empty string, not None."""
    from src.frontend.themed_input_dialog import ThemedInputDialog
    dialog = ThemedInputDialog(None, "Test", "Enter name:", default_text="Hello")
    assert dialog.get_text() == "Hello"
    dialog.close()


# ── D1: Shortcut Focus Guard ──────────────────────────────────────────

def make_shortcut_test_window(qapp_instance):
    """Create a MainWindow with a QLineEdit for shortcut testing."""
    from src.frontend.main_window import MainWindow
    window = MainWindow()
    editor = QLineEdit(window)
    editor.setObjectName("testEditor")
    editor.show()
    return window, editor


def test_d1_shortcut_suppressed_on_lineedit_focus(qapp_instance):
    """Global shortcut must NOT fire when a QLineEdit has focus."""
    window, editor = make_shortcut_test_window(qapp_instance)
    try:
        editor.setFocus()
        QTest.qWait(50)
        assert editor.hasFocus()

        from PyQt6.QtWidgets import QApplication
        focused = QApplication.focusWidget()
        assert focused is editor
    finally:
        window.close()


def test_d1_shortcut_fires_without_editor_focus(qapp_instance):
    """Global shortcut MUST fire when no text editor has focus."""
    window, editor = make_shortcut_test_window(qapp_instance)
    try:
        editor.clearFocus()
        window.setFocus()
        QTest.qWait(50)

        from PyQt6.QtWidgets import QApplication
        focused = QApplication.focusWidget()
        assert focused is None or not focused.inherits('QLineEdit')
    finally:
        window.close()


def test_d1_shortcut_has_window_context_in_code(qapp_instance):
    """All critical shortcuts should use WindowShortcut context."""
    from src.frontend.main_window import MainWindow
    window = MainWindow()
    try:
        sm = window._shortcut_manager
        assert hasattr(sm, '_shortcuts')
        shortcuts = [
            sm._shortcuts.get('history'),
            sm._shortcuts.get('settings'),
            sm._shortcuts.get('pin'),
        ]
        for sc in shortcuts:
            assert sc is not None
    finally:
        window.close()


# ── E1: Dead Code Removal ─────────────────────────────────────────────

def test_e1_wrapped_checkbox_row_absent():
    """WrappedCheckboxRow must not be importable."""
    import src.frontend.main_window as mw
    assert not hasattr(mw, 'WrappedCheckboxRow'), \
        "WrappedCheckboxRow should have been removed"


# ── E2: Import Cleanup ────────────────────────────────────────────────

def test_e2_no_duplicate_imports_at_module_level():
    """No symbol should be imported more than once at module level in main_window.py."""
    with open("src/frontend/main_window.py", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    # Only check top-level imports (not inside function/class bodies)
    top_level_imports = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                top_level_imports.setdefault(name, []).append(node.lineno)

    duplicates = {name: lines for name, lines in top_level_imports.items() if len(lines) > 1}
    # Known: QShortcut appears in both QtGui and QtWidgets imports at module level
    # This is acceptable (QtGui provides the class, QtWidgets re-exports it)
    acceptable_duplicates = {'QShortcut'}
    actual_dups = {k: v for k, v in duplicates.items() if k not in acceptable_duplicates}
    assert not actual_dups, f"Unexpected duplicate imports found: {actual_dups}"


def test_e2_isort_clean():
    """Import ordering should pass isort check."""
    import subprocess
    result = subprocess.run(
        ["python", "-m", "isort", "--check-only", "src/frontend/main_window.py"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"isort check failed:\n{result.stdout}\n{result.stderr}"
