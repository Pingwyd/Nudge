# Sprint 11 — Crash Report Client

**Date:** 2026-06-20
**Version Target:** v1.11.0
**Status:** PLANNING

---

## Problem

Crash dialog shows raw stack trace. Not user-friendly.

## Approach

- Redesign crash_dialog.py with empathetic error screen
- Collapse raw stack trace into "Technical Details" expandable drawer
- Add "Restart" button (relaunches app)
- Add "Send Report" button (copies crash details to clipboard)
- Show friendly error message, not technical jargon

## Chunks

| Chunk | Description | Type | Model | Depends On |
|-------|-------------|------|-------|------------|
| F1-C1 | Redesign crash dialog UI | Structural | MiMo | — |
| F1-C2 | Add Restart and Send Report buttons | Mechanical | DeepSeek | C1 |
| F1-C3 | Add Technical Details expandable drawer | Structural | MiMo | C1 |

## Acceptance Criteria

- Crash screen shows friendly error message
- Technical Details drawer expands to show stack trace
- "Restart" button relaunches the application
- "Send Report" button copies crash details to clipboard
- Dialog matches glass theme in all modes
