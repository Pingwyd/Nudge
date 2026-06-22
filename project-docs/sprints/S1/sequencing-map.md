# Sprint 1 — Sequencing Map

## Parallel vs. Sequential

```
S1-F1-C1 (Smooth drag: architecture analysis)  ──┐
                                                   ├──► S1-F1-C2 (Smooth drag: implement)
S1-F2-C1 (Undo toast: convert to child widget)  ──┤
                                                   │
S1-F3-C1 (Confirmation dialogs: wire into actions) ┘
```

## Detailed Dependencies

| PROMPT ID | Description | Depends On | Can Run In Parallel With |
|-----------|-------------|------------|--------------------------|
| S1-F1-C1 | Smooth drag: architecture analysis | None | S1-F2-C1, S1-F3-C1 |
| S1-F1-C2 | Smooth drag: implement batch move | S1-F1-C1 | S1-F2-C1, S1-F3-C1 |
| S1-F2-C1 | Undo toast: convert to child widget | None | S1-F1-C1, S1-F1-C2, S1-F3-C1 |
| S1-F3-C1 | Confirmation dialogs: wire ThemedMessageDialog | None | S1-F1-C1, S1-F1-C2, S1-F2-C1 |

## Execution Order

**Wave 1 (parallel):** S1-F1-C1, S1-F2-C1, S1-F3-C1
**Wave 2 (after S1-F1-C1 completes):** S1-F1-C2

**Total waves:** 2
**Critical path:** S1-F1-C1 → S1-F1-C2

## Notes

- S1-F1-C1 is architecture-reasoning (MiMo) and must complete before S1-F1-C2 (implementation, DeepSeek).
- S1-F2-C1 and S1-F3-C1 are independent of each other and of the S1-F1 chain.
- All three features modify different files or different sections of main_window.py, so parallel execution is safe.
