# Sprint 7 — Settings Modernization

**Date:** 2026-06-20
**Version Target:** v1.11.0
**Status:** PLANNING

---

## Problem

Settings sidebar lacks visual appeal. Theme selection is plain text. Toggle switches are default OS style.

## Approach

- Add icons to sidebar navigation items (General, Appearance, Shortcuts, Export, Reminders, Advanced, Help)
- Create grid-card layout for theme selection (Dark, Light, OLED as visual cards with preview)
- Implement iOS-style toggle switches for boolean settings

## Chunks

| Chunk | Description | Type | Model | Depends On |
|-------|-------------|------|-------|------------|
| F1-C1 | Add icons to sidebar navigation | Structural | MiMo | — |
| F1-C2 | Create theme grid-card selection | Structural | MiMo | — |
| F1-C3 | Implement iOS-style toggle switches | Structural | MiMo | — |
| F1-C4 | Apply theme-aware styling to all new widgets | Mechanical | DeepSeek | C1, C2, C3 |

## Acceptance Criteria

- Sidebar shows icon + text for each settings tab
- Theme selection displays as visual grid-cards with preview
- Boolean settings use iOS-style toggle switches
- All new widgets respect Dark/Light/OLED themes
- Shortcut recorder still works as before
