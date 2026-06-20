# S1 Sequencing Map

```
S1-F1-C1 ──► S1-F1-C2 ──► S1-F1-C3
     (MiMo)      (DeepSeek)    (MiMo)

S1-F2-C1 ──► S1-F2-C2 ──► S1-F2-C3
     (MiMo)      (DeepSeek)    (MiMo)

═══════════════════════════════════
F1 and F2 are INDEPENDENT
Can run in parallel.
═══════════════════════════════════
```

| Chunk | Model | Parallel? |
|-------|-------|-----------|
| S1-F1-C1 | MiMo | yes (with S1-F2-C1) |
| S1-F1-C2 | DeepSeek | no (after C1) |
| S1-F1-C3 | MiMo | no (after C2) |
| S1-F2-C1 | MiMo | yes (with S1-F1-C1) |
| S1-F2-C2 | DeepSeek | no (after C1) |
| S1-F2-C3 | MiMo | no (after C2) |
