# Releases

User-facing release notes for Nudge.

---

## v2.0.0 — Clipboard Import, Sound Effects, History Revamp

### New Features
- Clipboard import — press Ctrl+Shift+V to paste multiple lines, each becomes a task
- Optional completion sound when tasks are checked off (toggle in Settings)
- Stats bar in History showing total, today, and yesterday counts
- Card-style task rows in History with rounded corners
- Collapse chevrons on History time period sections
- Ctrl+F to focus the tag filter dropdown
- Real-time task search from the title bar

### Improvements
- History tab sorted most-recent-first within each time period
- Smaller, better-proportioned buttons in confirmation dialogs
- 20 UI files cleaned up with centralized spacing/sizing constants
- Bold divider after last high-priority task for clearer separation
- "HIGH PRIORITY" header auto-removes when all high-priority tasks are completed

### Bug Fixes
- History count badge updates correctly when tasks are deleted
- History tab updates live when tasks are completed while open
- Footer task count now updates when tasks are added or removed
- Confirmation dialog buttons no longer clipped at bottom edge
- Group dropdown populates correctly on app restart

---

## v1.14.0 — Priority View, Drag-and-Drop Import

### New Features
- Flat list priority view with "HIGH PRIORITY" header and divider
- Drag-and-drop import — drop text, URLs, or files to create tasks
- Drop indicator overlay shows the drop zone during drag

### Improvements
- History shortcut (Ctrl+H) now toggles — closes dialog if already open
- Reminders shortcut (Alt+R) is now configurable in Settings → Shortcuts
- Reminders popup toggles on shortcut press with proper overlap avoidance
- Footer history button restyled with visible border and larger size
- Footer separator and task count update colors on theme switch
- Shortcut suppression only applies when the main input bar has focus

### Bug Fixes
- History shortcut no longer blocked by dialog search bars
- Reminders dialog no longer stacks on repeated shortcut presses
- Reminders shortcut default persists correctly after save
- Footer border visible in all themes (dark, light, OLED)
- Footer task count text readable in light mode

---

## v1.13.0 — Checkboxes, Due Dates, Tags, Recurring Tasks

### New Features
- Task checkboxes to mark tasks complete
- Due dates with colored chips
- Priority indicators with high-priority flag
- Tags with 8-color palette picker
- Recurring tasks (daily, weekly, monthly)
- Tag filter dropdown
- Font selection in Settings
- History retention setting
- Reminders popup (Alt+R)
- Footer bar with task count and History shortcut
- Updated tutorial covering all new features

### Improvements
- Redesigned History dialog with search, trash icon, timestamps
- Unified button styles across all dialogs
- Overflow menu divider between utility and community links
- Smoother glass panel drag
- Shorter confirmation messages for destructive actions

### Bug Fixes
- QComboBox dropdown theming via QPalette
- Tag filter combo background matches theme
- Tag color picker closes on focus loss
- Crash dialog emoji clipping and details toggle
- Settings remembers last tab
- Windows notifications use correct app icon
- TaskRowWidget theme refresh for all elements
- QFont::setPointSize warning resolved
- Footer bar and History button positioning
- Tag filter search matches group names

---

## v1.12.0 — Non-Blocking Updates

### New Features
- Non-blocking update download with background progress
- Install prompt after download completes
- Cached update downloads for retry

### Bug Fixes
- Progress bar stuck at 0%
- File lock errors on retry
- PowerShell download timeout with retry logic
- Progress bar cycling past 100MB

---

## v1.11.0 — Liquid Glass Upgrade

### New Features
- Frosted glass panels with drop shadows and glow effects
- Mouse-following glass shine over task list
- SVG toolbar icons for Settings and History
- Input glow on focus
- Live appearance preview for sliders and toggles

### Improvements
- Settings and History buttons use themed SVG icons
- DWM shadow fix for clean window corners

### Bug Fixes
- Transparent background on first launch
- Text size slider applies live without Save
- Dev runner handles crashes gracefully

---

## v1.10.0 — Group Drag-Reorder, History Search

### New Features
- Group drag-reorder with drop indicator
- History search bar
- History "Don't ask to delete" checkbox
- Clear All button in History
- Undo toast dismiss button
- Horizontal scroll for task input

### Improvements
- Undo toast width increased for longer messages

### Bug Fixes
- Group drag not starting (QPushButton capturing events)
- Group drop indicator invisible
- QLineEdit crash from invalid scroll bar policy

---

## v1.9.0 — Live Countdown, Double-Click Restore

### New Features
- Live countdown timer on tasks with active reminders
- Double-click to restore in History panel

### Improvements
- Settings → Reminders moved to dedicated tab
- Reset to Defaults resets only active tab
- Undo Toast rendered inside app window

### Bug Fixes
- Drag stutter resolved with deferred-move coalescing
- Confirmation dialogs for all destructive actions
- Entry widget theming for Dark/Light/OLED themes

---

## v1.0.0 — First Release

### Features
- Liquid-glass task widget with frosted acrylic panels
- Dark, light, and OLED themes
- Task list with inline add, edit, delete, reordering, and groups
- Persistent state with portable mode
- Settings dialog with all options
- History panel for completed tasks
- Export to .txt, .md, and .csv
- Windows toast notifications
- Keyboard shortcuts
- CI/CD pipeline with tagged releases
