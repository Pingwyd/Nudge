# Sprint 9 — Liquid Glass Aesthetic Upgrade

**Date:** 2026-06-20
**Version Target:** v1.11.0
**Status:** PLANNING

---

## Problem

Current theme styling is functional but lacks premium feel. No glows, shadows, or dynamic icons.

## Approach

- Add subtle glow effects on focused inputs and buttons
- Add premium drop shadows on dialogs and cards
- Create programmatic SVG icons that adjust color per theme (light/dark/OLED)
- Cache rendered icons for performance

## Chunks

| Chunk | Description | Type | Model | Depends On |
|-------|-------------|------|-------|------------|
| F1-C1 | Add glow/shadow effects to theme.py | Structural | MiMo | — |
| F1-C2 | Create SVG icon generators | Structural | MiMo | — |
| F1-C3 | Apply icons to toolbar buttons | Mechanical | DeepSeek | C2 |
| F1-C4 | Cache rendered icons | Mechanical | DeepSeek | C2 |

## Acceptance Criteria

- Focused inputs show subtle glow effect
- Dialogs/cards have drop shadows
- SVG icons adjust color when switching themes
- Icons are crisp at all sizes (16px, 24px, 32px)
- No startup performance regression (icons cached)
