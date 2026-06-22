# Sprint 12 — Hover Glow Animation

**Date:** 2026-06-20
**Version Target:** v1.11.0
**Status:** PLANNING

---

## Problem

Main panel lacks interactive visual feedback. No sense of "glass" material.

## Approach

- Add "Glass Shine" animation that follows mouse cursor on main panel
- Subtle radial gradient or glow effect that moves with cursor
- Effect is subtle — reinforces glass metaphor without being distracting
- Use `QGraphicsEffect` or custom `paintEvent` overlay

## Chunks

| Chunk | Description | Type | Model | Depends On |
|-------|-------------|------|-------|------------|
| F1-C1 | Create GlassShineEffect class | Structural | MiMo | — |
| F1-C2 | Apply effect to main tasks panel | Mechanical | DeepSeek | C1 |
| F1-C3 | Make effect optional (performance) | Mechanical | DeepSeek | C1 |

## Acceptance Criteria

- Subtle glow follows cursor on main panel
- Effect is visible in Dark and OLED themes (less visible in Light)
- No performance impact with smooth cursor tracking
- Effect disabled if user has reduced motion preference (if detectable)
