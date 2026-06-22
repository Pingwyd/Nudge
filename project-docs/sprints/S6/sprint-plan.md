# Sprint 6 — Double-Click Ambiguity (Tooltips + Feedback)

**Date:** 2026-06-20
**Version Target:** v1.11.0
**Status:** PLANNING

---

## Problem

Double-clicking a task toggles it as "done" (main window) or restores it (history), but there's no visual indicator that double-clicking does anything. Users only look for checkboxes.

## Approach

- Add tooltip on task hover in main window: "Double-click to complete"
- Add tooltip on task hover in history: "Double-click to restore"
- Add subtle visual feedback on double-click: brief flash/highlight animation on the row

## Chunks

| Chunk | Description | Type | Model | Depends On |
|-------|-------------|------|-------|------------|
| F1-C1 | Add hover tooltips to TaskRowWidget | Mechanical | DeepSeek | — |
| F1-C2 | Add hover tooltips to HistoryRowWidget | Mechanical | DeepSeek | — |
| F1-C3 | Add double-click flash animation | Structural | MiMo | C1, C2 |

## Acceptance Criteria

- Hovering over a task in main window shows "Double-click to complete" tooltip
- Hovering over a task in history shows "Double-click to restore" tooltip
- Double-clicking a task produces a brief visual flash/highlight (200-300ms)
- Tooltip matches glass theme styling
- No performance impact with many tasks
