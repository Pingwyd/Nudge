# Sprint 10 — Information Density (Visual Cards)

**Date:** 2026-06-20
**Version Target:** v1.11.0
**Status:** PLANNING

---

## Problem

General Settings tab is a long list of checkboxes without visual grouping. Hard to scan.

## Approach

- Group General tab settings into visual cards:
  - **Startup & System:** Run on Startup, Check for Updates
  - **Window Behavior:** Lock Position, Pin, Always on Top
- Cards have subtle border, background, and header
- Use card component from Sprint 7 (Settings Modernization)

## Chunks

| Chunk | Description | Type | Model | Depends On |
|-------|-------------|------|-------|------------|
| F1-C1 | Create SettingsCardWidget component | Structural | MiMo | — |
| F1-C2 | Group General tab settings into cards | Mechanical | DeepSeek | C1 |

## Acceptance Criteria

- General tab shows grouped visual cards
- Each card has a header and relevant settings
- Cards match glass theme styling
- Settings values still persist correctly
