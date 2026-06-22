# Sprint 8 — History Chronological Headers + Group Badges

**Date:** 2026-06-20
**Version Target:** v1.11.0
**Status:** PLANNING

---

## Problem

History list is a flat list of completed tasks. Users can't quickly find tasks from a specific day or group.

## Approach

- Group completed tasks under collapsible chronological headers (Today, Yesterday, This Week, Older)
- Render colorful group badges instead of bracketed text `[Group]`
- Headers are collapsible (click to expand/collapse)

## Chunks

| Chunk | Description | Type | Model | Depends On |
|-------|-------------|------|-------|------------|
| F1-C1 | Create chronological grouping logic | Structural | MiMo | — |
| F1-C2 | Create collapsible header widgets | Structural | MiMo | C1 |
| F1-C3 | Replace bracketed text with colorful group badges | Mechanical | DeepSeek | — |

## Acceptance Criteria

- Tasks grouped under Today, Yesterday, This Week, Older headers
- Headers are collapsible (click toggles visibility)
- Group badges show group name with group color background
- Existing search still filters across all groups
- "Clear All" still clears all entries regardless of group
