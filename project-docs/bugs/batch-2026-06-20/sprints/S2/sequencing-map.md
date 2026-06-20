# S2 Sequencing Map

```
S2-F1-C1 ──► S2-F1-C2
   (DeepSeek)    (MiMo)

S2-F2-C1 ──► S2-F2-C2 ──► S2-F2-C3
     (MiMo)      (DeepSeek)    (MiMo)

S2-F3-C1 ──► S2-F3-C2
   (DeepSeek)    (MiMo)

═══════════════════════════════════
F1, F2, and F3 are INDEPENDENT
Can run in parallel.
═══════════════════════════════════
```

| Chunk | Model | Parallel? |
|-------|-------|-----------|
| S2-F1-C1 | DeepSeek | yes (with F2-C1, F3-C1) |
| S2-F1-C2 | MiMo | no (after C1) |
| S2-F2-C1 | MiMo | yes (with F1-C1, F3-C1) |
| S2-F2-C2 | DeepSeek | no (after C1) |
| S2-F2-C3 | MiMo | no (after C2) |
| S2-F3-C1 | DeepSeek | yes (with F1-C1, F2-C1) |
| S2-F3-C2 | MiMo | no (after C1) |
