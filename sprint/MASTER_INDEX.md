# Nudge — Master Execution Plan

## Priority Order (feed into OpenCode sequentially)

```
A1 — Single-Instance Handler         [Architecture / Critical]
   sprint/A1_SingleInstance/prompt.md

A2 — Horizontal Scaling Improvement  [UI Usability / Critical]
   sprint/A2_HorizontalScaling/prompt.md

B1 — Crash Log Client                [Error Recovery / High]
   sprint/B1_CrashReporter/prompt.md

C1 — Timer / Reminder System         [Core Feature / High]
   sprint/C1_Timers/prompt.md

D1 — Changelog Button in Settings    [UX Polish / Medium]
   sprint/D1_ChangelogButton/prompt.md

D2 — Release Notes After Update      [UX Polish / Medium]
   sprint/D2_ReleaseNotes/prompt.md

E1 — Animations (Fade In/Out)        [Visual Polish / Low]
   sprint/E1_Animations/prompt.md
```

## Architecture Rules (all prompts)
- Three-layer: `backend/` (data+logic) → `frontend/` (UI) → `main_window.py` (composition)
- No circular imports
- Thread-safe I/O: QThread or signals for background work
- Theme-aware: use `theme.py` tokens, never raw colors
- No hardcoded config strings: use `appstate.json` via `state_manager.py`
- Read file before editing, make minimal changes
- Test both dark and light themes after each change