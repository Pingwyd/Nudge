# Sprint 3 — Sequencing Map

## Parallel vs. Sequential

```
S3-F1-C1 (Countdown indicator)  ──┐
                                    ├──► (both can run in parallel)
S3-F2-C1 (Double-click restore) ──┘
```

## Detailed Dependencies

| PROMPT ID | Description | Depends On | Can Run In Parallel With |
|-----------|-------------|------------|--------------------------|
| S3-F1-C1 | Countdown indicator in TaskRowWidget | S2 complete | S3-F2-C1 |
| S3-F2-C1 | Double-click restore in History | None (independent) | S3-F1-C1 |

## Execution Order

**Wave 1 (parallel):** S3-F1-C1, S3-F2-C1

**Total waves:** 1
**Critical path:** None (both chunks are independent)

## Notes

- S3-F1-C1 is architecture-reasoning (MiMo) because it involves timer lifecycle, layout integration, and performance considerations.
- S3-F2-C1 is trivial UI (DeepSeek) — just changing a signal name and two text strings.
- Both modify different files (main_window.py vs history_row.py + one line in main_window.py), so no conflicts.
- S3-F1-C1 is the larger, more complex chunk. S3-F2-C1 is a 5-minute task.
