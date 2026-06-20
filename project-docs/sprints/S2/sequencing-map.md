# Sprint 2 — Sequencing Map

## Parallel vs. Sequential

```
S2-F1-C1 (Reset to Defaults: per-tab dispatcher) ──┐
                                                     ├──► S2-F3-C1 (Theme fix: apply tokens)
S2-F2-C1 (Reminders: own tab)  ────────────────────┘         │
                                                              ▼
                                                     S2-F3-C2 (Theme fix: add generators)
```

## Detailed Dependencies

| PROMPT ID | Description | Depends On | Can Run In Parallel With |
|-----------|-------------|------------|--------------------------|
| S2-F1-C1 | Reset to Defaults: per-tab dispatcher | S1 complete | S2-F2-C1 |
| S2-F2-C1 | Reminders: extract into own tab | S1 complete | S2-F1-C1 |
| S2-F3-C1 | Theme fix: apply tokens to entry widgets | S2-F2-C1 (new tab must exist) | None |
| S2-F3-C2 | Theme fix: add generators to theme.py | S2-F3-C1 (need to know missing tokens) | None |

## Execution Order

**Wave 1 (parallel):** S2-F1-C1, S2-F2-C1
**Wave 2 (after Wave 1):** S2-F3-C1
**Wave 3 (after S2-F3-C1):** S2-F3-C2

**Total waves:** 3
**Critical path:** S2-F2-C1 → S2-F3-C1 → S2-F3-C2

## Notes

- S2-F1-C1 and S2-F2-C1 modify different parts of SettingsDialog (reset button vs. tab structure), so they can run in parallel.
- S2-F3-C1 must wait for S2-F2-C1 because the new Reminders tab needs theming.
- S2-F3-C2 must wait for S2-F3-C1 to know which generators are actually missing.
- If S2-F3-C1 finds that all needed generators already exist, S2-F3-C2 becomes a no-op.
