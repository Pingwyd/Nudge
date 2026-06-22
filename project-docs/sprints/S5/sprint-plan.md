# Sprint 5 — Reminders Drawer (Prototype)

**Date:** 2026-06-20
**Version Target:** v1.11.0
**Status:** PLANNING

---

## Problem

Users want the Reminders list to feel like part of the main app, not a separate floating window or a buried Settings tab. A sliding drawer provides a cohesive, app-integrated feel.

## Approach

- Create a `DrawerWidget` that slides out from the left side of the main window
- The drawer overlays the task list (floats on top)
- Shows pending reminders with task name, countdown, and cancel button
- Animated slide-in/slide-out using `QPropertyAnimation` on `maximumWidth`
- Drawer opens via a button in the chrome bar (toolbar)
- Drawer state persisted (open/closed) across sessions

## Chunks

| Chunk | Description | Type | Model | Depends On |
|-------|-------------|------|-------|------------|
| F1-C1 | Create DrawerWidget class with slide animation | Structural | MiMo | — |
| F1-C2 | Add chrome bar button + wire to drawer | Mechanical | DeepSeek | C1 |
| F1-C3 | Populate drawer with reminders from TimerManager | Structural | MiMo | C1 |
| F1-C4 | Persist drawer state (open/closed) in appstate | Mechanical | DeepSeek | C2 |

## Dependency Graph

```
C1 ──→ C2 ──→ C4
 └──→ C3
```

## Acceptance Criteria

- Drawer slides in from left with smooth animation
- Shows all pending reminders with task name and countdown
- Cancel button removes reminder from TimerManager
- Drawer does NOT replace Settings Reminders tab (both exist for now)
- Drawer state (open/closed) persists across sessions
- Works in Dark, Light, and OLED themes

## Files Modified

- `src/frontend/main_window.py` — new `DrawerWidget` class, chrome bar button
- `src/frontend/theme.py` — drawer styling
- `src/backend/state_manager.py` — drawer state persistence

## Regression Risk

- **Low.** Add-only feature. No existing code removed or modified (except chrome bar layout).
