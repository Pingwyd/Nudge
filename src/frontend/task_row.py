"""Task row widget for rendering individual tasks."""

from datetime import datetime

from PyQt6.QtCore import QByteArray, QMimeData, QPoint, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QDrag, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QLineEdit,
                             QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

from src.frontend.due_date_chip import DueDateChip
from src.frontend.priority_indicator import PriorityIndicator
from src.frontend.responsive_text import (ResponsiveTextRowHelper,
                                          apply_editor_field_width,
                                          fix_single_line_editor_height,
                                          label_content_height,
                                          sync_stacked_page_height)
from src.frontend.tag_color_picker import TagColorPopup
from src.frontend.tag_pill_widget import TagPillWidget, get_tag_color
from src.frontend.theme import get_theme, normalize_theme_id
from src.frontend.widget_context import WidgetContext
from src.constants import (
    TASK_CHECKBOX_INDICATOR,
    TASK_ROW_CHECKBOX_SIZE,
    TASK_ROW_MARGINS,
)


class TaskRowWidget(QWidget):
    """One task row: compact height, scroll area absorbs extra space — not individual rows."""

    _checkbox_style_cache: dict[str, str] = {}

    def __init__(
        self,
        text,
        checked=False,
        text_size=14,
        on_toggled=None,
        on_commit=None,
        on_context_menu=None,
        content_indent=0,
        parent=None,
    ):
        super().__init__(parent)
        self.on_toggled = on_toggled
        self.on_commit = on_commit
        self.on_context_menu = on_context_menu
        self._is_section_end = False
        self._editing = False
        self._indent_spacer = None
        self._ctx: WidgetContext | None = None
        self._task_ref = None
        self._drag_start_pos = None
        self._tag_pills = []
        self._pending_tags = None
        self._pending_due_date = None
        self._group_section = None
        self.setToolTip("Double-click to edit")

        # Horizontal fill only; vertical size comes from content, not leftover list height.
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*TASK_ROW_MARGINS)
        layout.setSpacing(8)

        if content_indent > 0:
            self._indent_spacer = QWidget()
            self._indent_spacer.setFixedWidth(content_indent)
            self._indent_spacer.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            layout.addWidget(self._indent_spacer)

        # Checkbox — aligned to top so it sits next to the first line of text
        self._checkbox = QCheckBox()
        self._checkbox.setChecked(checked)
        self._checkbox.stateChanged.connect(lambda state: self._handle_toggled(state == Qt.CheckState.Checked.value))
        self._checkbox.setFixedSize(TASK_ROW_CHECKBOX_SIZE, TASK_ROW_CHECKBOX_SIZE)
        self._checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_theme_checkbox()
        layout.addWidget(self._checkbox, 0, Qt.AlignmentFlag.AlignVCenter)

        # Text — takes all remaining horizontal space
        self.content_stack = QStackedWidget()
        self.content_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        display_page = QWidget()
        display_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        display_layout = QHBoxLayout(display_page)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(0)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        display_layout.addWidget(self.label, 1)

        edit_page = QWidget()
        edit_page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        edit_layout = QHBoxLayout(edit_page)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        edit_layout.setSpacing(0)

        self.editor = QLineEdit(text)
        self.editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.editor.returnPressed.connect(self.commit_edit)
        self.editor.setDragEnabled(True)
        edit_layout.addWidget(self.editor, 1)

        self.content_stack.addWidget(display_page)
        self.content_stack.addWidget(edit_page)
        layout.addWidget(self.content_stack, 1)

        # Right-side badges — Preferred so they recalculate when children appear
        self._badges = QWidget()
        self._badges.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        badges_lay = QHBoxLayout(self._badges)
        badges_lay.setContentsMargins(0, 0, 0, 0)
        badges_lay.setSpacing(4)
        badges_lay.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._priority_indicator = PriorityIndicator()
        self._priority_indicator.setFixedSize(14, 14)
        badges_lay.addWidget(self._priority_indicator)

        self._tags_container = QWidget()
        self._tags_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._tags_layout = QHBoxLayout(self._tags_container)
        self._tags_layout.setContentsMargins(0, 0, 0, 0)
        self._tags_layout.setSpacing(3)
        self._tags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        badges_lay.addWidget(self._tags_container)
        self._tags_container.hide()

        self._due_date_chip = DueDateChip()
        self._due_date_chip.setFixedHeight(18)
        badges_lay.addWidget(self._due_date_chip)

        self._countdown_label = QLabel()
        self._countdown_label.setStyleSheet("font-size: 10px; color: transparent; background: transparent; border: none;")
        self._countdown_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._countdown_label.setFixedHeight(14)
        self._countdown_label.hide()
        badges_lay.addWidget(self._countdown_label)

        layout.addWidget(self._badges, 0, Qt.AlignmentFlag.AlignVCenter)

        self._countdown_timer = QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._update_countdown)

        reserved = []
        if self._indent_spacer is not None:
            reserved.insert(0, self._indent_spacer)
        reserved.append(self._checkbox)
        reserved.append(self._badges)
        self._text_layout = ResponsiveTextRowHelper(
            self, self.label, reserved, editor=self.editor
        )
        self._text_layout.set_content_stack(self.content_stack)
        self.set_text_size(text_size)
        QTimer.singleShot(0, self.sync_text_layout)

    def set_text_size(self, text_size, *, sync: bool = True):
        from PyQt6.QtGui import QFont
        font = self.label.font()
        font.setPixelSize(text_size)
        font.setWeight(QFont.Weight.Medium)
        self.label.setFont(font)
        self._task_text_size = int(text_size)
        self._refresh_label_stylesheet()
        editor_font = self.editor.font()
        editor_font.setPixelSize(text_size)
        self.editor.setFont(editor_font)
        self.editor.setStyleSheet(f"font-size: {int(text_size)}px;")
        if sync:
            self.sync_text_layout()

    def set_task_font(self, font_name, *, sync: bool = True):
        """Set the font family for the task text."""
        from PyQt6.QtGui import QFont
        if font_name == "Default (System)":
            font_name = None

        font = self.label.font()
        if font_name:
            font.setFamily(font_name)
        else:
            font.setFamily("")
        font.setWeight(QFont.Weight.Medium)
        self.label.setFont(font)

        editor_font = self.editor.font()
        if font_name:
            editor_font.setFamily(font_name)
        else:
            editor_font.setFamily("")
        self.editor.setFont(editor_font)
        if sync:
            self.sync_text_layout()

    def apply_search_highlight(self, query: str, match_kind: str = "task") -> None:
        """Soft amber wash on matches; optional Task·/Tag· type label while searching."""
        import html
        plain = self._task_ref.get("text", self.label.text()) if self._task_ref else self.label.text()
        if not query:
            self.label.setTextFormat(Qt.TextFormat.PlainText)
            self.label.setText(plain)
            self._refresh_label_stylesheet()
            self._apply_done_style(self._checkbox.isChecked())
            return
        theme_id = self._ctx.get_theme_id() if self._ctx else "dark"
        theme = get_theme(theme_id)
        bg = theme["colors"].get("search_match_bg", "rgba(245, 166, 35, 45)")
        muted = theme["colors"].get("text_muted", "rgba(255,255,255,180)")
        lower = plain.lower()
        q = query.lower()
        parts = []
        start = 0
        while True:
            idx = lower.find(q, start)
            if idx < 0:
                parts.append(html.escape(plain[start:]))
                break
            parts.append(html.escape(plain[start:idx]))
            match = html.escape(plain[idx:idx + len(query)])
            parts.append(
                f'<span style="background-color:{bg}; border-radius:3px;">{match}</span>'
            )
            start = idx + len(query)
        # Tag-only matches: still highlight task text if query appears; else plain + label
        body = "".join(parts) if q in lower else html.escape(plain)
        kind = "Tag" if match_kind == "tag" else "Task"
        size = getattr(self, "_task_text_size", 14)
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setText(
            f'<span style="font-size:{size}px; font-weight:500;">'
            f'<span style="color:{muted};">{kind} · </span>{body}</span>'
        )

    def _refresh_label_stylesheet(self) -> None:
        size = getattr(self, "_task_text_size", 14)
        if self.label.textFormat() == Qt.TextFormat.RichText:
            self.label.setStyleSheet("background: transparent; border: none;")
        else:
            self.label.setStyleSheet(f"font-size: {int(size)}px; font-weight: 500;")

    def _apply_done_style(self, done: bool) -> None:
        """Strikethrough + muted text while checked (briefly before archive)."""
        if self.label.textFormat() == Qt.TextFormat.RichText:
            return
        size = getattr(self, "_task_text_size", 14)
        if done:
            theme_id = self._ctx.get_theme_id() if self._ctx else "dark"
            muted = get_theme(theme_id)["colors"].get("text_muted", "rgba(255,255,255,160)")
            self.label.setStyleSheet(
                f"font-size: {size}px; font-weight: 500; color: {muted}; "
                "text-decoration: line-through; background: transparent; border: none;"
            )
        else:
            self._refresh_label_stylesheet()

    def _handle_toggled(self, checked):
        self._apply_done_style(checked)
        if self.on_toggled:
            self.on_toggled(checked)

    def update_theme(self, theme_id: str | None = None) -> None:
        """Refresh theme-dependent row chrome after a global theme change."""
        if theme_id is None:
            theme_id = self._ctx.get_theme_id() if self._ctx else "dark"
        else:
            theme_id = normalize_theme_id(theme_id)
        self._apply_theme_checkbox(theme_id)
        self._due_date_chip.update_theme(theme_id)
        if self._task_ref:
            self._priority_indicator.set_priority(
                self._task_ref.get("priority"),
                theme_id,
            )
        self._apply_countdown_theme()
        self.update()

    def _apply_theme_checkbox(self, theme_id: str | None = None):
        """Apply checkbox style for task rows — no padding so indicator isn't clipped."""
        if theme_id is None:
            theme_id = "dark"
        else:
            theme_id = normalize_theme_id(theme_id)
        # Cache compiled QSS per theme — rebuilding it for every row is slow.
        cache = TaskRowWidget._checkbox_style_cache
        css = cache.get(theme_id)
        if css is None:
            theme = get_theme(theme_id)
            from src.frontend.theme import _c, _r, generate_svg_icon
            import base64
            ind = TASK_CHECKBOX_INDICATOR
            on_accent = _c(theme, "on_accent")
            check_svg = generate_svg_icon("check", on_accent, ind)
            check_b64 = base64.b64encode(check_svg.encode("utf-8")).decode("ascii")
            check_url = f"data:image/svg+xml;base64,{check_b64}"
            css = f"""
            QCheckBox {{
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
                spacing: 0px;
            }}
            QCheckBox::indicator {{
                width: {ind}px;
                height: {ind}px;
                border-radius: {_r(theme, "checkbox")}px;
                border: 1px solid {_c(theme, "checkbox_border")};
                background-color: {_c(theme, "checkbox_indicator")};
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {_c(theme, "accent")};
            }}
            QCheckBox::indicator:checked {{
                background-color: {_c(theme, "checkbox_checked")};
                border: 1px solid {_c(theme, "accent")};
                image: url({check_url});
            }}
            """
            cache[theme_id] = css
        self._checkbox.setStyleSheet(css)

    def paintEvent(self, event):
        """Draw a separator line at the bottom — QSS border is overridden by glassPanel."""
        super().paintEvent(event)
        from src.constants import SECTION_DIVIDER_HEIGHT
        theme_id = self._ctx.get_theme_id() if self._ctx else "dark"
        theme = get_theme(theme_id)
        if self._is_section_end:
            color = theme["colors"].get("section_divider", "rgba(255, 255, 255, 80)")
            height = SECTION_DIVIDER_HEIGHT
        else:
            color = theme["colors"].get("separator", "rgba(255, 255, 255, 35)")
            height = 1
        painter = QPainter(self)
        painter.setPen(QPen(QColor(color), height))
        painter.drawLine(0, self.height() - height, self.width(), self.height() - height)
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Do not sync_text_layout here. Window resize already fires this for
        # every row on every mouse move; MainWindow debounces a single pass.

    def _update_badges_layout(self):
        """Recalculate badges width and invalidate parent layout.

        Called after badge children (priority, due_date, tags) change visibility
        so the HBoxLayout re-queries the badges sizeHint and gives the text
        column the correct remaining width.
        """
        # Force badges to report correct size based on visible children
        self._badges.adjustSize()
        hint = self._badges.sizeHint()
        # Use setMaximumWidth so badges can shrink at minimum window size
        self._badges.setMaximumWidth(hint.width())
        if self.layout() is not None:
            self.layout().invalidate()
        # Re-sync text width now that badges claimed their space
        QTimer.singleShot(0, self.sync_text_layout)

    def sync_text_layout(self):
        width = self._text_layout.sync_layout()
        self._sync_content_stack_height(text_col_width=width)

    def _sync_content_stack_height(self, text_col_width=None):
        """Content stack height accounts for full wrapped text height."""
        if self._editing:
            column_width = max(1, text_col_width or self.content_stack.width())
            apply_editor_field_width(self.editor, column_width)
            fix_single_line_editor_height(self.editor)
            sync_stacked_page_height(self.content_stack, self.editor.height())
        else:
            col = max(1, text_col_width or self.label.width() or self.content_stack.width())
            label_height = label_content_height(self.label, col)
            sync_stacked_page_height(self.content_stack, label_height)

    def begin_edit(self):
        if self._editing:
            return
        self._editing = True
        self.editor.setText(self.label.text())
        self.content_stack.setCurrentIndex(1)
        self.content_stack.updateGeometry()
        self.updateGeometry()
        self.sync_text_layout()
        QTimer.singleShot(0, lambda: (
            self.editor.setFocus(),
            self.editor.selectAll()
        ))

    def commit_edit(self):
        if not self._editing:
            self.begin_edit()
            return

        new_text = self.editor.text().strip()
        if not new_text:
            self.editor.setFocus()
            self.editor.selectAll()
            return

        self.label.setText(new_text)
        self._editing = False
        self.content_stack.setCurrentIndex(0)
        self.content_stack.updateGeometry()
        self.updateGeometry()
        if self.on_commit:
            self.on_commit(new_text)
        self.sync_text_layout()

    def toggle_edit_mode(self):
        if self._editing:
            self.commit_edit()
        else:
            self.begin_edit()

    def set_task_ref(self, task_ref):
        self._task_ref = task_ref
        self._update_row_from_task()

    def update_task(self, task, group_section=None, on_toggled=None, on_commit=None, on_context_menu=None):
        """Update this row with new task data, reusing existing child widgets."""
        self._task_ref = task
        self._group_section = group_section
        if on_toggled is not None:
            self.on_toggled = on_toggled
        if on_commit is not None:
            self.on_commit = on_commit
        if on_context_menu is not None:
            self.on_context_menu = on_context_menu
        self._update_row_from_task()

    def _update_row_from_task(self):
        """Update visual state from _task_ref, deferring expensive child creation."""
        if self._task_ref is None:
            return
        task = self._task_ref

        # Update checkbox
        self._checkbox.blockSignals(True)
        self._checkbox.setChecked(task.get("done", False))
        self._checkbox.blockSignals(False)

        # Update text label
        self.label.setText(task.get("text", ""))

        # Update priority indicator
        theme_id = self._ctx.get_theme_id() if self._ctx else "dark"
        self._priority_indicator.set_priority(task.get("priority"), theme_id)

        # Update tags — defer pill creation until visible
        self._update_tags_lazy(task.get("tags", []))

        # Update due date — defer chip creation until visible
        self._update_due_date_lazy(task.get("dueDate"))

        # Update countdown
        has_reminder = False
        if self._ctx is not None:
            cfg = self._ctx.get_timer_for_task(task["id"])
            if cfg is not None and cfg.enabled:
                has_reminder = True
        if has_reminder:
            self._start_countdown()
        else:
            self._stop_countdown()

        # Force layout recalc. Never call show() here — unparented rows become
        # top-level windows (ghost frames). Layout addWidget shows when needed.
        self._update_badges_layout()

    def _update_tags_lazy(self, tags):
        """Store pending tags; create pills only if row is visible."""
        self._pending_tags = tags
        if not self.isVisible():
            return
        self._initialize_tags(tags)

    def _initialize_tags(self, tags):
        """Actually create tag pill widgets for the given tags."""
        if not tags:
            for pill in self._tag_pills:
                self._tags_layout.removeWidget(pill)
                pill.deleteLater()
            self._tag_pills.clear()
            self._tags_container.hide()
            self._update_badges_layout()
            return

        custom_colors = self._task_ref.get("tagColors", {}) if self._task_ref else {}

        # Remove excess existing pills
        while len(self._tag_pills) > len(tags):
            pill = self._tag_pills.pop()
            self._tags_layout.removeWidget(pill)
            pill.deleteLater()

        # Create or reuse pills
        for i, tag in enumerate(tags):
            color = get_tag_color(tag, custom_colors)
            if i < len(self._tag_pills):
                pill = self._tag_pills[i]
                pill.update_tag(tag, color)
            else:
                pill = TagPillWidget(tag, color)
                pill.color_change_requested.connect(self._on_tag_color_change)
                self._tags_layout.addWidget(pill)
                self._tag_pills.append(pill)
            pill.show()

        self._tags_container.adjustSize()
        self._tags_container.show()
        self._update_badges_layout()

    def _update_due_date_lazy(self, due_date):
        """Store pending due date; set on chip only if row is visible."""
        self._pending_due_date = due_date
        if not self.isVisible():
            return
        self._initialize_due_date(due_date)

    def _initialize_due_date(self, due_date):
        """Set due date on existing chip, or hide it."""
        theme_id = self._ctx.get_theme_id() if self._ctx else "dark"
        if due_date:
            self._due_date_chip.set_due_date(due_date, theme_id)
            self._due_date_chip.show()
        else:
            self._due_date_chip.hide()
            self._due_date_chip.set_due_date(None, theme_id)
        self._update_badges_layout()

    def _on_tag_color_change(self, tag_name: str):
        """Handle tag color change request - show inline floating palette."""
        if not self._task_ref or not self._ctx:
            return
        
        # Find the pill widget for this tag
        pill_widget = None
        for i in range(self._tags_layout.count()):
            item = self._tags_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, TagPillWidget) and w._tag_name == tag_name:
                    pill_widget = w
                    break
        
        if not pill_widget:
            return
        
        # Get current color
        custom_colors = self._task_ref.get("tagColors", {})
        current_color = custom_colors.get(tag_name, get_tag_color(tag_name))
        
        # Show inline floating palette near the pill
        popup = TagColorPopup(current_color, self.window())
        popup.color_selected.connect(lambda color: self._apply_tag_color(tag_name, color))
        popup.popup_above(pill_widget)

    def _apply_tag_color(self, tag_name: str, color: str):
        """Apply new color to a tag."""
        if not self._task_ref:
            return
        
        # Initialize tagColors dict if needed
        if "tagColors" not in self._task_ref:
            self._task_ref["tagColors"] = {}
        
        self._task_ref["tagColors"][tag_name] = color
        
        # Save task
        if self._ctx:
            self._ctx.save_tasks(self._ctx.get_tasks())
        
        # Re-render pills
        self._render_tag_pills()

    def _start_countdown(self):
        if not self._countdown_timer.isActive():
            self._apply_countdown_theme()
            self._update_countdown()
            self._countdown_timer.start()

    def _stop_countdown(self):
        if self._countdown_timer.isActive():
            self._countdown_timer.stop()
        self._countdown_label.hide()
        self._countdown_label.setStyleSheet("font-size: 10px; color: transparent; background: transparent; border: none;")
        self._update_badges_layout()

    def _update_countdown(self):
        trigger_at = None
        if self._ctx is not None:
            cfg = self._ctx.get_timer_for_task(self._task_ref["id"])
            if cfg is not None:
                trigger_at = cfg.next_trigger_at
        if trigger_at is None:
            self._stop_countdown()
            return
        remaining = int(trigger_at - datetime.now().timestamp())
        if remaining <= 0:
            self._stop_countdown()
            return
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        seconds = remaining % 60
        if hours > 0:
            text = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            text = f"{minutes}m {seconds}s"
        else:
            text = f"{seconds}s"
        self._countdown_label.setText(text)
        self._countdown_label.show()
        self._update_badges_layout()

    def _apply_countdown_theme(self):
        parent = self.parent()
        theme_id = "dark"
        if parent and hasattr(parent, "app_state"):
            theme_id = normalize_theme_id(parent.app_state.get("theme", "dark"))
        theme = get_theme(theme_id)
        accent = theme["colors"].get("accent", "#F5A623")
        self._countdown_label.setStyleSheet(
            f"font-size: 10px; color: {accent}; background: transparent; border: none;"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._task_ref is not None:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (self._drag_start_pos is not None and
            event.buttons() & Qt.MouseButton.LeftButton):
            delta = event.position().toPoint() - self._drag_start_pos
            if delta.manhattanLength() > 10:
                drag = QDrag(self)
                mime = QMimeData()
                mime.setData("application/x-nudge-task-row", QByteArray())
                task_text = self._task_ref.get("text", "") if self._task_ref else ""
                mime.setText(task_text)
                drag.setMimeData(mime)
                pix = self.grab()
                # Lifted ghost: slightly larger canvas, soft shadow, offset draw
                margin = 6
                ghost = QPixmap(pix.width() + margin * 2, pix.height() + margin * 2)
                ghost.fill(Qt.GlobalColor.transparent)
                p = QPainter(ghost)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                shadow = QColor(0, 0, 0, 70)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(shadow))
                p.drawRoundedRect(margin + 2, margin + 3, pix.width(), pix.height(), 6, 6)
                p.setOpacity(0.92)
                p.translate(1, -1)  # subtle lift offset
                p.drawPixmap(margin, margin, pix)
                p.end()
                drag.setPixmap(ghost)
                drag.setHotSpot(delta + QPoint(margin, margin))
                scroll = None
                if self._ctx is not None and hasattr(self._ctx, "scroll_area"):
                    scroll = self._ctx.scroll_area
                timer = None
                if scroll is not None:
                    timer = QTimer(self)
                    timer.setInterval(40)

                    def _tick(sc=scroll):
                        from PyQt6.QtGui import QCursor
                        vp = sc.viewport()
                        local = vp.mapFromGlobal(QCursor.pos())
                        edge = 36
                        bar = sc.verticalScrollBar()
                        if local.y() < edge:
                            bar.setValue(bar.value() - 18)
                        elif local.y() > vp.height() - edge:
                            bar.setValue(bar.value() + 18)

                    timer.timeout.connect(_tick)
                    timer.start()
                drag.exec(Qt.DropAction.MoveAction)
                if timer is not None:
                    timer.stop()
                    timer.deleteLater()
                self._drag_start_pos = None
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._editing:
            return super().mouseReleaseEvent(event)
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._editing:
            return super().mouseDoubleClickEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.begin_edit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def contextMenuEventFromChild(self, global_pos):
        if self.on_context_menu:
            self.on_context_menu(global_pos)

    def contextMenuEvent(self, event):
        if self.on_context_menu:
            self.on_context_menu(event.globalPos())
            event.accept()
            return
        super().contextMenuEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if self._pending_tags is not None:
            self._initialize_tags(self._pending_tags)
            self._pending_tags = None
        if self._pending_due_date is not None:
            self._initialize_due_date(self._pending_due_date)
            self._pending_due_date = None
