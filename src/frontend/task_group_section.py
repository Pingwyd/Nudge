"""
Inline accordion section for one task group (Stage 6).
"""

from __future__ import annotations

from typing import Callable, List, Optional

from PyQt6.QtCore import QEvent, QMimeData, QPoint, Qt
from PyQt6.QtGui import QDrag, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class TaskGroupSection(QWidget):
    """Collapsible group header plus a vertical list of task row widgets."""

    def __init__(
        self,
        group: dict,
        task_count: int,
        text_size: int = 14,
        on_toggle_expanded: Optional[Callable[[str, bool], None]] = None,
        on_header_context_menu: Optional[Callable[[str, object], None]] = None,
        on_header_clicked: Optional[Callable[[str], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.group = group
        self.group_id = group["id"]
        self.on_toggle_expanded = on_toggle_expanded
        self.on_header_context_menu = on_header_context_menu
        self._on_header_clicked = on_header_clicked
        self._expanded = bool(group.get("expanded", True))
        self.task_rows: List[QWidget] = []
        self._main_window = None
        self._drag_hover_index = -1
        self._drag_start_pos = None
        self._is_dragging = False
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 4)
        root.setSpacing(4)

        chevron = "▼" if self._expanded else "▶"
        self.header_btn = QPushButton(f"{chevron}  {group.get('name', 'Group')}  ({task_count})")
        self.header_btn.setObjectName("groupHeader")
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn.clicked.connect(self._toggle)
        self.header_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.header_btn.customContextMenuRequested.connect(self._open_header_menu)
        self.header_btn.installEventFilter(self)
        root.addWidget(self.header_btn)

        self.content = QWidget()
        self.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(6)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content.setVisible(self._expanded)
        root.addWidget(self.content)

        self._drop_indicator = QFrame(self.content)
        self._drop_indicator.setObjectName("dropIndicator")
        self._drop_indicator.setFixedHeight(3)
        self._drop_indicator.hide()

        font = self.header_btn.font()
        font.setPointSize(text_size)
        self.header_btn.setFont(font)

    def _toggle(self):
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        chevron = "▼" if self._expanded else "▶"
        name = self.group.get("name", "Group")
        count = len(self.task_rows)
        self.header_btn.setText(f"{chevron}  {name}  ({count})")
        if self.on_toggle_expanded:
            self.on_toggle_expanded(self.group_id, self._expanded)
        if self._on_header_clicked:
            self._on_header_clicked(self.group_id)

    def _open_header_menu(self, pos):
        if self.on_header_context_menu:
            self.on_header_context_menu(self.group_id, self.header_btn.mapToGlobal(pos))

    def eventFilter(self, obj, event):
        if obj is self.header_btn and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_start_pos = event.position().toPoint()
                self._is_dragging = False
                return True
        elif obj is self.header_btn and event.type() == QEvent.Type.MouseMove:
            if (self._drag_start_pos is not None and
                event.buttons() & Qt.MouseButton.LeftButton):
                delta = event.position().toPoint() - self._drag_start_pos
                if delta.manhattanLength() > 10:
                    self._is_dragging = True
                    self._start_group_drag()
                    self._drag_start_pos = None
                    return True
        elif obj is self.header_btn and event.type() == QEvent.Type.MouseButtonRelease:
            if self._is_dragging:
                self._is_dragging = False
                self._drag_start_pos = None
                return True
            self._drag_start_pos = None
            self._toggle()
            return True
        return super().eventFilter(obj, event)

    def _start_group_drag(self):
        mw = self._main_window
        if mw is None:
            return
        groups_enabled = mw.app_state.get("groupsEnabled", True)
        if not groups_enabled:
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData("application/x-nudge-group", self.group_id.encode())
        group_name = self.group.get("name", "Group")
        task_texts = [r._task_ref.get("text", "") for r in self.task_rows if hasattr(r, "_task_ref")]
        mime.setText(f"{group_name}\n" + "\n".join(f"- {t}" for t in task_texts))
        drag.setMimeData(mime)
        pix = self.header_btn.grab()
        ghost = QPixmap(pix.size())
        ghost.fill(Qt.GlobalColor.transparent)
        p = QPainter(ghost)
        p.setOpacity(0.55)
        p.drawPixmap(0, 0, pix)
        p.end()
        drag.setPixmap(ghost)
        drag.setHotSpot(QPoint(pix.width() // 2, pix.height()))
        drag.exec(Qt.DropAction.MoveAction)

    def add_task_row(self, row_widget: QWidget, index: int | None = None) -> None:
        if index is not None:
            self.content_layout.insertWidget(index, row_widget, 0, Qt.AlignmentFlag.AlignTop)
            self.task_rows.insert(index, row_widget)
        else:
            self.content_layout.addWidget(row_widget, 0, Qt.AlignmentFlag.AlignTop)
            self.task_rows.append(row_widget)

    def remove_task_row(self, row_widget: QWidget) -> None:
        self.content_layout.removeWidget(row_widget)
        row_widget.setParent(None)
        row_widget.deleteLater()
        if row_widget in self.task_rows:
            self.task_rows.remove(row_widget)

    def refresh(self, tasks: list, text_size: int = 14, main_window=None) -> None:
        """Clear and repopulate this section's task rows from a task list.

        # FIX-A1: targeted section update — does not call render_tasks.
        """
        for row in list(self.task_rows):
            self.content_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self.task_rows.clear()
        if main_window is not None:
            from src.frontend.main_window import TaskRowWidget
            for task in tasks:
                row = TaskRowWidget(
                    task["text"],
                    checked=task.get("done", False),
                    text_size=text_size,
                    on_toggled=lambda checked, t=task: main_window.toggle_task(t, checked),
                    on_commit=lambda new_text, t=task: main_window.update_task_text(t, new_text),
                    on_context_menu=lambda global_pos, t=task: main_window.show_task_context_menu(t),
                    content_indent=8,
                )
                row._task_ref = task
                main_window.task_row_widgets[id(task)] = row
                self.add_task_row(row)
            self.refresh_header_count()

    def refresh_header_count(self) -> None:
        chevron = "▼" if self._expanded else "▶"
        name = self.group.get("name", "Group")
        self.header_btn.setText(f"{chevron}  {name}  ({len(self.task_rows)})")

    def force_layout(self) -> None:
        """Force recalculation of all nested layouts so rows have correct geometry."""
        layout = self.layout()
        if layout is not None:
            layout.activate()
        self.content_layout.activate()

    def sync_task_text_layouts(self) -> None:
        for row in self.task_rows:
            if hasattr(row, "sync_text_layout"):
                row.sync_text_layout()

    def _drop_index_at(self, pos):
        """Insertion index from drop y-position (pos is in section coords)."""
        content_pos = self.content.mapFrom(self, pos)
        visible = [w for w in self.task_rows if w is not None and not w.isHidden()]
        for i, w in enumerate(visible):
            if content_pos.y() < w.y() + w.height() // 2:
                return i
        return len(visible)

    def _update_indicator(self):
        if self._drag_hover_index < 0 or not self._expanded:
            self._drop_indicator.hide()
            return
        visible = [w for w in self.task_rows if w is not None and not w.isHidden()]
        y_pos = 0
        if self._drag_hover_index < len(visible):
            y_pos = visible[self._drag_hover_index].y() - 1
        elif visible:
            last = visible[-1]
            y_pos = last.y() + last.height() - 1
        self._drop_indicator.move(0, max(0, y_pos))
        self._drop_indicator.setFixedWidth(self.content.width())
        self._drop_indicator.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-nudge-task-row"):
            source = event.source()
            if source is not None and hasattr(source, "_task_ref"):
                self._drag_hover_index = self._drop_index_at(event.position().toPoint())
                self._update_indicator()
                event.acceptProposedAction()
                return
        elif event.mimeData().hasFormat("application/x-nudge-group"):
            mw = self._main_window
            if mw is not None:
                pos = self.mapTo(mw.tasks_widget, event.position().toPoint())
                mw._update_group_drop_indicator(pos)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-nudge-task-row"):
            self._drag_hover_index = self._drop_index_at(event.position().toPoint())
            self._update_indicator()
            event.acceptProposedAction()
            return
        elif event.mimeData().hasFormat("application/x-nudge-group"):
            mw = self._main_window
            if mw is not None:
                pos = self.mapTo(mw.tasks_widget, event.position().toPoint())
                mw._update_group_drop_indicator(pos)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._drag_hover_index = -1
        self._drop_indicator.hide()
        mw = self._main_window
        if mw is not None:
            mw._group_drop_indicator.hide()

    def dropEvent(self, event):
        self._drag_hover_index = -1
        self._drop_indicator.hide()
        mw = self._main_window
        if event.mimeData().hasFormat("application/x-nudge-group"):
            if mw is not None:
                pos = self.mapTo(mw.tasks_widget, event.position().toPoint())
                mw._on_group_drop(pos, event.mimeData())
            event.acceptProposedAction()
            return
        source = event.source()
        if source is None or not hasattr(source, "_task_ref"):
            return
        insert_index = self._drop_index_at(event.position().toPoint())
        if mw is not None:
            mw._on_row_dropped(source, self.group_id, insert_index)
        event.acceptProposedAction()
