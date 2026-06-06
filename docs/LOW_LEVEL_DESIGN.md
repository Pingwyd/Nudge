# Low-Level Design (LLD) & Tracking Document
**Application:** Windows Desktop Task Widget
**Tech Stack:** Python, PyQt6, winotify, Win32 API (ctypes)

This document serves as both a detailed architecture reference and a living checklist to track implementation progress. Update the `[ ]` checkboxes to `[x]` as components are built.

---

## 1. Data Models

### 1.1 `Task`
Represents a single actionable item.
- `id` (UUID): Unique identifier.
- `text` (String): The actual task description.
- `done` (Boolean): Completion status.
- `createdAt` (Datetime): Timestamp of creation.
- `order` (Integer): For drag-and-drop reordering.

### 1.2 `TaskList`
Groups tasks, primarily used for the daily boot reminder.
- `date` (String YYYY-MM-DD): The date these tasks represent.
- `tasks` (Array of `Task`): List of tasks.
- `lastSeen` (Datetime): Last interaction or boot time.
- `version` (Integer): Schema version for future migrations.

### 1.3 `AppState`
Stores the UI and OS-level configurations.
- `windowPos` (Object `{x, y}`): Coordinates of the widget.
- `windowSize` (Object `{w, h}`): Dimensions of the widget.
- `pinned` (Boolean): Whether it is pinned to the desktop (below icons).
- `startOnBoot` (Boolean): Registry run-on-startup toggle.

---

## 2. Frontend Layer (PyQt6 UI)
The user interface layer resting on top of the OS Desktop layer.

### 2.1 Input Bar
- **Description:** A text input field mapped to submit on `Enter`.
- **Logic:** Takes free-text, splits by period `"."`, trims whitespace, and emits to `ParsedTasks[]`.
- **Status:** [x] Implemented

### 2.2 Checklist View
- **Description:** The main scrollable list of tasks.
- **Logic:** Iterates over `Task[]` rendering checkboxes and text labels. Listens to completion toggles.
- **Status:** [x] Implemented

### 2.3 Context Menu
- **Description:** Right-click menu on individual tasks and the general list.
- **Features:**
  - Edit text (Implemented)
  - Reorder items (Move Up/Move Down Implemented)
  - Delete individual task (Implemented)
  - Clear all completed tasks (Implemented)
  - Exit App (Implemented)
- **Status:** [x] Implemented

### 2.4 Boot Reminder Banner
- **Description:** In-app visual indicator showing pending items from the previous session.
- **Logic:** Triggered by the backend `BootChecker`.
- **Status:** [ ] Not Implemented

### 2.5 Settings Panel
- **Description:** General configuration UI UI.
- **Toggles:**
  - Startup on boot (Implemented).
  - Opacity/Transparency slider (Implemented).
  - Pin position lock (Implemented).
- **Status:** [x] Implemented

### 2.6 Visual Design & Theme (Liquid Glass / Glassmorphism)
- **Description:** The overarching UI style mimicking Apple's Liquid Glass/Acrylic look.
- **Characteristics:** 
  - Translucent backgrounds with soft background blur.
  - Subtle semi-transparent borders and highlights to simulate physical glass.
  - Drop shadows for depth separation from the desktop wallpaper.
- **Technical Approach (PyQt6):** Use frameless windows with transparent backgrounds (`Qt.WindowType.FramelessWindowHint`, `Qt.WidgetAttribute.WA_TranslucentBackground`) mixed with custom QPainter styling, QGraphicsBlurEffect, or native Windows 11 Acrylic/Mica API wrappers (if supported on the host OS).
- **Status:** [ ] Not Implemented

---

## 3. Backend / Main Thread Layer

### 3.1 InputParser
- **Inputs:** Raw string from Frontend Input Bar.
- **Operations:** `split(".")` -> `trim` -> `filter empty strings`.
- **Outputs:** An array of new `Task` objects equipped with newly generated UUIDs and current timestamps.
- **Status:** [x] Implemented

### 3.2 TaskStore
- **Description:** The intermediary between memory and persistent storage.
- **Operations:**
  - `load()`: Reads `tasks.json`.
  - `save()` / `update()`: Modifies memory and triggers atomic writes (e.g., write to temporary file, then rename to `tasks.json` to prevent corruption).
- **Status:** [x] Implemented

### 3.3 BootChecker
- **Description:** Evaluates task statuses upon application launch.
- **Logic:** Compares `createdAt` parsing to today's date. If they are older and incomplete, it emits a Toast Notification via winotify.
- **Status:** [x] Implemented

### 3.4 StateManager
- **Description:** Manages window preferences and interacts with the OS.
- **Logic:** Reads/writes `appstate.json`. Calls OS layer for pinning and positioning updates. Adds/removes registry keys.
- **Status:** [x] Partially Implemented

---

## 4. OS Integration Layer

### 4.1 Desktop Pin (The "Widget Layer")
- **Mechanism:** Uses Python `ctypes` and Win32 API.
- **Logic:** Finds the `WorkerW` background class window, then calls `SetParent(app_window_hwnd, workerw_hwnd)` to permanently embed the app below desktop icons.
- **Status:** [x] Implemented

### 4.2 Startup Entry
- **Mechanism:** Windows Registry.
- **Logic:** Write string payload to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- **Status:** [x] Implemented

### 4.3 Toast Notification
- **Mechanism:** `winotify` (or `plyer`) library.
- **Logic:** Fires OS-level notification on device boot/app launch if unchecked tasks exist.
- **Status:** [x] Implemented

---

## 5. Persistent Store (File System)
*Location: `%APPDATA%\TaskApp\` or user-defined directory.*

- **`tasks.json`**: Managed by `TaskStore`.
  - **Status:** [ ] Not Implemented
- **`appstate.json`**: Managed by `StateManager`.
  - **Status:** [ ] Not Implemented

---

## 6. Main Data Flows

**Flow 1: Creating Tasks**
1. User types "Buy milk. Pay bills." in **Input Bar**.
2. **InputParser** receives string, splits into `["Buy milk", "Pay bills"]`.
3. Parser creates two `Task` objects, overriding UUIDs and timestamps.
4. **TaskStore** updates memory array.
5. **TaskStore** triggers Atomic disk write to `tasks.json`.
6. **Checklist View** re-renders.

**Flow 2: Notification on Boot**
1. PC starts -> Registry triggers app start (**Startup Entry**).
2. **TaskStore** loads `tasks.json`.
3. **BootChecker** evaluates `lastSeen`.
4. If unchecked tasks exist from yesterday -> Triggers **Toast Notification** & **Boot Reminder Banner**.

**Flow 3: Application Initialization**
1. App launches.
2. **StateManager** loads `appstate.json`.
3. Window size/position applied.
4. If `pinned == true`, invoke **Desktop Pin** Win32 functions.