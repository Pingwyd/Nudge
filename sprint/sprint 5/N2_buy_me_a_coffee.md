# N2 — Buy Me a Coffee Feature

## Files
- **NEW:** `C:\Users\Prosperr\Documents\_Remind\src\frontend\support_dialog.py`
- **MODIFY:** `C:\Users\Prosperr\Documents\_Remind\src\frontend\main_window.py`

---

## Part A: Create Support Dialog

Create `src/frontend/support_dialog.py`:

```python
"""Support / Buy Me a Coffee dialog."""
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QPixmap
from PyQt6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout)
from src.frontend.theme import get_theme, normalize_theme_id, refresh_glass_shells
from src import __app_name__, __version__

class SupportDialog(QDialog):
    """Display donation/support options."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None
        self.frame = None
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle(f"Support {__app_name__}")
        self.resize(360, 300)
        self.setMinimumSize(300, 260)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.frame = QFrame(self)
        self.frame.setObjectName("glassPanel")
        self.frame.setGeometry(0, 0, 360, 300)
        
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        
        title = QLabel(f"☕ Support {__app_name__}")
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel(
            f"{__app_name__} v{__version__} is free and open-source.\n"
            "If you find it useful, consider buying me a coffee!"
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)
        
        # Spacer
        layout.addStretch()
        
        # Donation buttons
        coffee_btn = QPushButton("☕ Buy Me a Coffee")
        coffee_btn.setObjectName("primaryButton")
        coffee_btn.setMinimumHeight(40)
        coffee_btn.clicked.connect(self._open_coffee_link)
        layout.addWidget(coffee_btn)
        
        # Optional: GitHub Sponsor button
        github_btn = QPushButton("⭐ Sponsor on GitHub")
        github_btn.setObjectName("ghostButton")
        github_btn.setMinimumHeight(36)
        github_btn.clicked.connect(self._open_github_sponsor)
        layout.addWidget(github_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _open_coffee_link(self):
        """Open Buy Me a Coffee page."""
        # Replace with your actual URL
        QDesktopServices.openUrl(QUrl("https://buymeacoffee.com/yourusername"))
    
    def _open_github_sponsor(self):
        """Open GitHub Sponsor page."""
        # Replace with your actual URL
        QDesktopServices.openUrl(QUrl("https://github.com/sponsors/yourusername"))
    
    # ... (add draggable mouse events, overlap opacity, resize event
    #      following same pattern as UpdateInfoDialog) ...
```

---

## Part B: Add Chrome Button

In `MainWindow.init_ui()` chrome button section, add a new button:

```python
self.btn_support = QPushButton("☕")
self.btn_support.setObjectName("chromeButton")
self.btn_support.setFixedSize(chrome_btn_sz, chrome_btn_sz)
self.btn_support.setToolTip("Support Nudge")
self.btn_support.setCursor(Qt.CursorShape.PointingHandCursor)
self.btn_support.clicked.connect(self._open_support_dialog)
top_bar.addWidget(self.btn_support)
```

Place it:
- Before `btn_feedback` (leftmost) — good visible position
- Or after `btn_settings` — near other settings-related buttons

Add method:
```python
def _open_support_dialog(self):
    dialog = SupportDialog(self)
    self._place_dialog_avoiding_rects(dialog, self._window_rects_to_avoid())
    dialog.exec()
```

---

## Part C: Optional Settings Tab Entry
Add a "Support Development" button in the Advanced tab of Settings:
```python
support_btn = QPushButton("☕ Support Development")
support_btn.setObjectName("primaryButton")
support_btn.setCursor(Qt.CursorShape.PointingHandCursor)
support_btn.clicked.connect(lambda: self._open_support_dialog())
advanced_layout.addWidget(support_btn)
```

---

## Code Quality
- **No data sent:** URLs are user-initiated (click required)
- **Follows existing patterns:** Same Liquid Glass styling, draggable, overlap detection
- **User-friendly:** Clear description of what the app is and why donate
- **URLs abstracted:** Easy to change donation links in one place

## Verification
- ☕ button visible in chrome bar
- Click → Support dialog opens with Liquid Glass styling
- "Buy Me a Coffee" → opens browser to donation page
- "Sponsor on GitHub" → opens GitHub sponsors
- Close button dismisses
- Dialog positioned to avoid overlap