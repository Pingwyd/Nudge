# S4 — Sequencing Map

## Dependency Graph

```
S4-F1-C1 ──→ S4-F2-C1
S4-F3-C1 (parallel)
S4-F4-C1 ──→ S4-F4-C2 ──→ S4-F4-C3
S4-F5-C1 (parallel)
```

## Parallelizable Waves

| Wave | Chunks | Rationale |
|------|--------|-----------|
| 1 | S4-F1-C1, S4-F3-C1, S4-F4-C1, S4-F5-C1 | All independent — different files, no dependencies |
| 2 | S4-F2-C1, S4-F4-C2 | F2-C1 depends on F1-C1 (search bar placement); F4-C2 depends on F4-C1 (architecture) |
| 3 | S4-F4-C3 | Verification after implementation |

## Critical Path

S4-F4-C1 → S4-F4-C2 → S4-F4-C3 (longest chain: 3 chunks)

## Non-Critical (can run in any order)

- S4-F1-C1, S4-F3-C1, S4-F5-C1 — all single-chunk features
