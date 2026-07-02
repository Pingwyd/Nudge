"""History dialog for viewing task history."""

from datetime import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.backend.icon import get_app_icon
from src.backend.task_groups import group_name
from src.frontend.collapsible_header import CollapsibleHeader
from src.frontend.frameless_chrome import FramelessChromeController
from src.frontend.glass_panel_dialog import GlassPanelDialog
from src.frontend.history_row import HistoryRowWidget
from src.frontend.themed_message_dialog import ThemedMessageDialog
from src.frontend.theme import (_r, get_theme, history_clear_all_button_stylesheet,
                                history_count_badge_stylesheet,
                                history_footer_stylesheet,
                                history_header_card_stylesheet,
                                history_search_bar_stylesheet,
                                history_title_stylesheet,
                                normalize_theme_id)
from src.constants import (FONT_SIZE_BODY, FONT_SIZE_LABEL_MD,
                           FONT_SIZE_LABEL_SM, FONT_SIZE_TITLE_MD,
                           HISTORY_CARD_SPACING, HISTORY_COUNT_BADGE_SIZE,
                           HISTORY_DIALOG_DEFAULT, HISTORY_DIALOG_MIN,
                           HISTORY_FOOTER_MARGINS, HISTORY_FOOTER_SPACING,
                           HISTORY_HEADER_CARD_MARGINS, HISTORY_HEADER_SPACING,
                           HISTORY_SEPARATOR_HEIGHT, HISTORY_STATS_BAR_MIN_HEIGHT,
                           HISTORY_STATS_GAP, RADIUS_PANEL, SPACING_LG)


class HistoryDialog(GlassPanelDialog):
    def __init__(self, history_store, restore_callback, groups_data=None, parent=None, state_manager=None):
        super().__init__(parent, overlap_radius=RADIUS_PANEL, escape_action="close")
        self.history_store = history_store
        self.restore_callback = restore_callback
        self.groups_data = groups_data or {"groups": []}
        self.rows = []
        self._history_tasks = []
        self.title_label = None
        self.count_badge = None
        self._chrome = None
        self._state_manager = state_manager
        self._empty_state_widget = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Task History")
        self.setWindowIcon(get_app_icon())
        if self._state_manager:
            w, h = self._state_manager.get_history_window_size()
        else:
            w, h = HISTORY_DIALOG_DEFAULT
        self.resize(w, h)
        self.setMinimumSize(*HISTORY_DIALOG_MIN)
        self.setMouseTracking(True)
        self._chrome = FramelessChromeController(self, min_width=HISTORY_DIALOG_MIN[0], min_height=HISTORY_DIALOG_MIN[1])

        self.bg_frame.setGeometry(0, 0, *HISTORY_DIALOG_DEFAULT)

        theme_id = self._get_theme_id()
        theme = get_theme(theme_id)
        c = theme["colors"]
        tc = c.get("text", "#ffffff")
        tmc = c.get("text_muted", "rgba(255,255,255,180)")
        border_c = c.get("border", "rgba(255,255,255,60)")
        input_bg = c.get("input_bg", "rgba(0,0,0,40)")
        accent = c.get("accent", "#4fc3f7")
        danger_text = c.get("danger_text", "#ff5555")

        layout = QVBoxLayout(self.bg_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header_card = QWidget()
        header_card.setStyleSheet(history_header_card_stylesheet(theme))
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(*HISTORY_HEADER_CARD_MARGINS)
        header_layout.setSpacing(HISTORY_HEADER_SPACING)

        title_row = QHBoxLayout()
        title_row.setSpacing(SPACING_LG)
        self.title_label = QLabel("Completed tasks")
        self.title_label.setStyleSheet(history_title_stylesheet(theme))
        title_row.addWidget(self.title_label)
        title_row.addStretch()
        self.count_badge = QLabel("0")
        self.count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_badge.setFixedSize(*HISTORY_COUNT_BADGE_SIZE)
        self.count_badge.setStyleSheet(history_count_badge_stylesheet(theme))
        title_row.addWidget(self.count_badge)
        header_layout.addLayout(title_row)

        hint = QLabel("Double-click any task to restore it.")
        hint.setStyleSheet(f"color: {tmc}; font-size: {FONT_SIZE_LABEL_MD}px; background: transparent; border: none;")
        header_layout.addWidget(hint)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search tasks or groups...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self._filter_history)
        self.search_bar.setStyleSheet(history_search_bar_stylesheet(theme))
        header_layout.addWidget(self.search_bar)

        layout.addWidget(header_card)
        layout.addSpacing(HISTORY_STATS_GAP)

        self._stats_bar = QLabel()
        self._stats_bar.setMinimumHeight(HISTORY_STATS_BAR_MIN_HEIGHT)
        self._stats_bar.setStyleSheet(f"color: {tmc}; font-size: {FONT_SIZE_LABEL_MD}px; font-weight: bold; background: transparent; border: none; padding: 2px 20px;")
        layout.addWidget(self._stats_bar)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.tasks_widget = QWidget()
        self.tasks_widget.setObjectName("transparentSurface")
        self.tasks_widget.setStyleSheet("background: transparent; border: none;")
        self.tasks_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tasks_layout.setSpacing(HISTORY_CARD_SPACING)

        self.scroll_area.setWidget(self.tasks_widget)
        layout.addWidget(self.scroll_area, stretch=1)

        self._empty_state_widget = QLabel("No completed tasks yet.")
        self._empty_state_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state_widget.setStyleSheet(f"color: {tmc}; font-size: {FONT_SIZE_BODY}px; padding: 20px 0; background: transparent; border: none;")
        layout.addWidget(self._empty_state_widget)
        self._empty_state_widget.hide()

        self.refresh_history()

        separator = QWidget()
        separator.setFixedHeight(HISTORY_SEPARATOR_HEIGHT)
        separator.setStyleSheet(f"background: {border_c};")
        layout.addWidget(separator)

        footer = QWidget()
        footer.setStyleSheet(history_footer_stylesheet(theme))
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(*HISTORY_FOOTER_MARGINS)
        footer_layout.setSpacing(HISTORY_FOOTER_SPACING)

        self.skip_delete_cb = QCheckBox("Skip confirmation")
        self.skip_delete_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_delete_cb.setStyleSheet(f"font-size: {FONT_SIZE_LABEL_SM}px; color: {tmc}; background: transparent; spacing: 6px;")
        if self._state_manager:
            skip = self._state_manager.state.get("historySkipDeleteConfirm", False)
            self.skip_delete_cb.setChecked(skip)
            self.skip_delete_cb.toggled.connect(self._on_skip_delete_toggled)
        footer_layout.addWidget(self.skip_delete_cb)

        footer_layout.addStretch()

        clear_all_btn = QPushButton("Clear all")
        clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_all_btn.setStyleSheet(history_clear_all_button_stylesheet(theme))
        clear_all_btn.clicked.connect(self.clear_all_history)
        footer_layout.addWidget(clear_all_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)

        layout.addWidget(footer)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_history_row_text_layouts()
        if self._state_manager and event.oldSize().isValid():
            self._state_manager.save_history_window_size(event.size().width(), event.size().height())

    def _get_theme_id(self):
        parent = self.parent()
        if parent is not None and hasattr(parent, "app_state"):
            return normalize_theme_id(parent.app_state.get("theme", "dark"))
        return "dark"

    def _filter_history(self, text):
        from src.frontend.history_row import HistoryRowWidget
        query = text.strip().lower()

        for i in range(self.tasks_layout.count()):
            widget = self.tasks_layout.itemAt(i).widget()
            if isinstance(widget, CollapsibleHeader):
                # Hide all children first, skip deleted C++ objects
                alive = []
                for child in widget._children:
                    try:
                        child.setVisible(False)
                        alive.append(child)
                    except RuntimeError:
                        pass
                widget._children = alive
                widget.setVisible(False)

        for row in self.rows:
            task_text = row.task_ref.get("text", "").lower()
            task_group = group_name(self.groups_data, row.task_ref.get("groupId")).lower()
            row.setVisible(not query or query in task_text or query in task_group)

        for i in range(self.tasks_layout.count()):
            widget = self.tasks_layout.itemAt(i).widget()
            if isinstance(widget, CollapsibleHeader):
                visible_rows = [c for c in widget._children if isinstance(c, HistoryRowWidget) and c.isVisible()]
                widget.setVisible(len(visible_rows) > 0)
                if visible_rows:
                    # Show separators only between two visible rows
                    for idx, child in enumerate(widget._children):
                        if not isinstance(child, HistoryRowWidget):
                            prev_visible = idx > 0 and isinstance(widget._children[idx - 1], HistoryRowWidget) and widget._children[idx - 1].isVisible()
                            next_visible = idx < len(widget._children) - 1 and isinstance(widget._children[idx + 1], HistoryRowWidget) and widget._children[idx + 1].isVisible()
                            child.setVisible(prev_visible and next_visible)

        filtered = [row.task_ref for row in self.rows if row.isVisible()]
        self._update_stats_bar(filtered)

    def _sync_history_row_text_layouts(self):
        for row in self.rows:
            if hasattr(row, "sync_text_layout"):
                row.sync_text_layout()

    def _group_by_time_period(self, entries):
        now = datetime.now()
        today = now.date()
        yesterday = today.fromordinal(today.toordinal() - 1)
        week_ago = today.fromordinal(today.toordinal() - 7)
        groups = {"Today": [], "Yesterday": [], "This Week": [], "Older": []}
        for entry in entries:
            try:
                completed_at = datetime.fromisoformat(entry.get("completedAt", ""))
                entry_date = completed_at.date()
            except (ValueError, TypeError):
                groups["Older"].append(entry)
                continue
            if entry_date == today:
                groups["Today"].append(entry)
            elif entry_date == yesterday:
                groups["Yesterday"].append(entry)
            elif entry_date >= week_ago:
                groups["This Week"].append(entry)
            else:
                groups["Older"].append(entry)
        return groups

    def _update_stats_bar(self, entries=None):
        if entries is None:
            entries = self._history_tasks
        groups = self._group_by_time_period(entries)
        total = len(entries)
        if total == 0:
            self._stats_bar.hide()
            return
        parts = [f"{total} total"]
        for period in ["Today", "Yesterday", "This Week", "Older"]:
            count = len(groups.get(period, []))
            if count > 0:
                parts.append(f"{period}: {count}")
        self._stats_bar.setText(" \u00b7 ".join(parts))
        self._stats_bar.show()

    def refresh_history(self):
        self.rows.clear()
        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        theme_id = self._get_theme_id()
        self._history_tasks = self.history_store.load()
        count = len(self._history_tasks)
        self.count_badge.setText(str(count))
        self.title_label.setText("Completed tasks")

        self._empty_state_widget.setVisible(count == 0)
        self.scroll_area.setVisible(count > 0)

        if count == 0:
            self.tasks_layout.addStretch(1)
            return

        filtered = self._get_filtered_entries(self._history_tasks) if hasattr(self, '_get_filtered_entries') else self._history_tasks
        groups = self._group_by_time_period(filtered)

        for period_name, period_entries in groups.items():
            if not period_entries:
                continue

            header = CollapsibleHeader(period_name, len(period_entries))
            self.tasks_layout.addWidget(header)

            for idx, task in enumerate(reversed(period_entries)):
                gname = group_name(self.groups_data, task.get("groupId"))
                completed_at = task.get("completedAt", "")
                time_str = ""
                try:
                    dt = datetime.fromisoformat(completed_at)
                    time_str = dt.strftime("%I:%M %p").lstrip("0") if dt.date() == datetime.now().date() else dt.strftime("%a \u00b7 %I:%M %p").lstrip("0")
                except (ValueError, TypeError):
                    pass

                row = HistoryRowWidget(
                    task.get("text", ""),
                    group_name=gname,
                    time_str=time_str,
                    text_size=FONT_SIZE_TITLE_MD,
                    on_restore=lambda t=task: self.restore_history_item(t),
                    on_delete=lambda t=task: self.delete_history_item(t),
                    theme_id=theme_id,
                )
                row.task_ref = task
                row._section_header = header
                self.tasks_layout.addWidget(row)
                self.rows.append(row)
                header.add_child(row)

                if idx < len(period_entries) - 1:
                    sep = QWidget()
                    sep.setFixedHeight(HISTORY_SEPARATOR_HEIGHT)
                    sep.setStyleSheet(f"background: {self._get_theme_colors().get('border', 'rgba(255,255,255,60)')}; margin: 0 12px;")
                    self.tasks_layout.addWidget(sep)
                    header.add_child(sep)

        self.tasks_layout.addStretch(1)
        self._update_stats_bar(filtered)
        QTimer.singleShot(0, self._sync_history_row_text_layouts)
        self.tasks_widget.setUpdatesEnabled(True)

    def _get_theme_colors(self):
        return get_theme(self._get_theme_id())["colors"]

    def add_external_archived_task(self, archived_task):
        """Insert a row for a task archived from the main window while dialog is open."""
        self._history_tasks.append(archived_task)
        gname = group_name(self.groups_data, archived_task.get("groupId"))
        completed_at = archived_task.get("completedAt", "")
        time_str = ""
        try:
            dt = datetime.fromisoformat(completed_at)
            time_str = dt.strftime("%I:%M %p").lstrip("0") if dt.date() == datetime.now().date() else dt.strftime("%a \u00b7 %I:%M %p").lstrip("0")
        except (ValueError, TypeError):
            pass

        row = HistoryRowWidget(
            archived_task.get("text", ""),
            group_name=gname,
            time_str=time_str,
            text_size=FONT_SIZE_TITLE_MD,
            on_restore=lambda t=archived_task: self.restore_history_item(t),
            on_delete=lambda t=archived_task: self.delete_history_item(t),
            theme_id=self._get_theme_id(),
        )
        row.task_ref = archived_task
        row._section_header = None
        self.rows.insert(0, row)

        # Find or create the "Today" section header
        today_header = None
        today_header_index = -1
        for i in range(self.tasks_layout.count()):
            item = self.tasks_layout.itemAt(i)
            w = item.widget() if item else None
            if isinstance(w, CollapsibleHeader) and w._title == "TODAY":
                today_header = w
                today_header_index = i
                break

        if today_header is None:
            # No "Today" section yet — create one at position 0 (after any stretch)
            today_header = CollapsibleHeader("Today", 0)
            self.tasks_layout.insertWidget(0, today_header)

        # Insert the row right after the header (at the end of existing rows in this section)
        insert_index = today_header_index + 1 if today_header_index >= 0 else 1
        # Walk past existing rows and separators belonging to this header
        for i in range(insert_index, self.tasks_layout.count()):
            w = self.tasks_layout.itemAt(i).widget() if self.tasks_layout.itemAt(i) else None
            if w is None:
                break
            if isinstance(w, CollapsibleHeader):
                break
            insert_index = i + 1

        self.tasks_layout.insertWidget(insert_index, row)
        row._section_header = today_header
        today_header.add_child(row)

        # Update header count — count all visible rows in this section
        section_rows = [r for r in self.rows if getattr(r, '_section_header', None) is today_header]
        today_header.update_count(len(section_rows))
        today_header.setVisible(True)

        self._empty_state_widget.hide()
        self.scroll_area.setVisible(True)
        self._filter_history(self.search_bar.text())
        self._update_stats_bar()
        QTimer.singleShot(0, self._sync_history_row_text_layouts)
        count = len(self._history_tasks)
        self.count_badge.setText(str(count))

    def restore_history_item(self, task_ref):
        self.restore_callback(task_ref)
        self._remove_row_for_task(task_ref)
        self._history_tasks = [t for t in self._history_tasks if t is not task_ref]
        self.history_store.save(self._history_tasks)
        count = len(self._history_tasks)
        self.count_badge.setText(str(count))
        self._update_stats_bar()
        if count == 0:
            self._empty_state_widget.setVisible(True)
            self.scroll_area.setVisible(False)

    def _on_skip_delete_toggled(self, checked):
        if self._state_manager:
            self._state_manager.state["historySkipDeleteConfirm"] = checked
            self._state_manager.save()

    def delete_history_item(self, task_ref):
        skip_confirm = self._state_manager.state.get("historySkipDeleteConfirm", False) if self._state_manager else False
        if not skip_confirm:
            if not ThemedMessageDialog.question(self, "Delete History Entry", "Are you sure you want to delete this history entry? This cannot be undone."):
                return
        self._remove_row_for_task(task_ref)
        self._history_tasks = [t for t in self._history_tasks if t is not task_ref]
        self.history_store.save(self._history_tasks)
        count = len(self._history_tasks)
        self.count_badge.setText(str(count))
        self._update_stats_bar()
        if count == 0:
            self._empty_state_widget.setVisible(True)
            self.scroll_area.setVisible(False)

    def _remove_row_for_task(self, task_ref):
        from PyQt6.QtWidgets import QWidget
        removed_header = None
        for row in list(self.rows):
            if row.task_ref is task_ref:
                removed_header = getattr(row, '_section_header', None)
                self.tasks_layout.removeWidget(row)
                if removed_header is not None and row in removed_header._children:
                    removed_header._children.remove(row)
                row.deleteLater()
                self.rows.remove(row)
                break
        self._cleanup_separators()

        if removed_header is not None:
            remaining = sum(1 for r in self.rows if getattr(r, '_section_header', None) is removed_header)
            removed_header.update_count(remaining)
            if remaining == 0:
                removed_header.setVisible(False)

        QTimer.singleShot(0, self._sync_history_row_text_layouts)

    def _cleanup_separators(self):
        from PyQt6.QtWidgets import QWidget
        to_remove = []
        for i in range(self.tasks_layout.count()):
            item = self.tasks_layout.itemAt(i)
            w = item.widget() if item else None
            if w is None or w in self.rows:
                continue
            if not isinstance(w, QWidget):
                continue
            # Check if it's a separator (thin widget, not a header)
            if hasattr(w, 'height') and w.height() <= 2 and not isinstance(w, CollapsibleHeader):
                # Check if it's between two rows or at the edge
                prev_is_row = i > 0 and self.tasks_layout.itemAt(i - 1).widget() in self.rows if self.tasks_layout.itemAt(i - 1) else False
                next_is_row = i < self.tasks_layout.count() - 1 and self.tasks_layout.itemAt(i + 1).widget() in self.rows if self.tasks_layout.itemAt(i + 1) else False
                if not (prev_is_row and next_is_row):
                    to_remove.append(w)
        for w in to_remove:
            self.tasks_layout.removeWidget(w)
            w.deleteLater()

    def clear_all_history(self):
        if not ThemedMessageDialog.question(self, "Clear History", "Clear ALL history entries? This cannot be undone."):
            return
        self.rows.clear()
        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._history_tasks = []
        self.history_store.save(self._history_tasks)
        self.count_badge.setText("0")
        self._update_stats_bar()
        self._empty_state_widget.setVisible(True)
        self.scroll_area.setVisible(False)
        self.tasks_layout.addStretch(1)
        self._sync_history_row_text_layouts()
