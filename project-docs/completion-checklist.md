# Completion Checklist

## Sprint 1 — Fix & Polish

- [ ] S1-F1-C1 — Smooth drag: architecture analysis (MiMo V2.5)
- [ ] S1-F1-C2 — Smooth drag: implement batch move (DeepSeek V4 Flash)
- [ ] S1-F2-C1 — Undo toast: convert to child widget (DeepSeek V4 Flash)
- [ ] S1-F3-C1 — Confirmation dialogs: wire ThemedMessageDialog (DeepSeek V4 Flash)

## Sprint 2 — Settings Restructure

- [ ] S2-F1-C1 — Reset to Defaults: per-tab dispatcher (DeepSeek V4 Flash)
- [ ] S2-F2-C1 — Reminders: extract into own tab (DeepSeek V4 Flash)
- [ ] S2-F3-C1 — Theme fix: apply tokens to entry widgets (DeepSeek V4 Flash)
- [ ] S2-F3-C2 — Theme fix: add generators to theme.py (DeepSeek V4 Flash)

## Sprint 3 — New Features

- [ ] S3-F1-C1 — Countdown indicator in TaskRowWidget (MiMo V2.5)
- [ ] S3-F2-C1 — Double-click restore in History (DeepSeek V4 Flash)

## Sprint 4 — History UX, Group Drag, Input Scroll

- [ ] S4-F1-C1 — History delete confirmation bypass + Clear All button (DeepSeek V4 Flash)
- [ ] S4-F2-C1 — History live search filter (DeepSeek V4 Flash)
- [ ] S4-F3-C1 — Undo toast dismiss button (DeepSeek V4 Flash)
- [ ] S4-F4-C1 — Group drag architecture (MiMo V2.5)
- [ ] S4-F4-C2 — Group drag implementation (DeepSeek V4 Flash)
- [ ] S4-F4-C3 — Group drag verification (MiMo V2.5)
- [ ] S4-F5-C1 — Input bar horizontal scrolling (DeepSeek V4 Flash)

## Sprint 5 — Reminders Drawer (Prototype)

- [ ] S5-F1-C1 — Create DrawerWidget class (MiMo)
- [ ] S5-F1-C2 — Add chrome bar button (DeepSeek)
- [ ] S5-F1-C3 — Populate drawer with reminders (MiMo)
- [ ] S5-F1-C4 — Persist drawer state (DeepSeek)

## Sprint 6 — Double-Click Ambiguity

- [ ] S6-F1-C1 — Add hover tooltips to TaskRowWidget (DeepSeek)
- [ ] S6-F1-C2 — Add hover tooltips to HistoryRowWidget (DeepSeek)
- [ ] S6-F1-C3 — Add double-click flash animation (MiMo)

## Sprint 7 — Settings Modernization

- [ ] S7-F1-C1 — Add icons to sidebar navigation (MiMo)
- [ ] S7-F1-C2 — Create theme grid-card selection (MiMo)
- [ ] S7-F1-C3 — Implement iOS-style toggle switches (MiMo)
- [ ] S7-F1-C4 — Apply theme-aware styling (DeepSeek)

## Sprint 8 — History Chronological Headers + Group Badges

- [ ] S8-F1-C1 — Create chronological grouping logic (MiMo)
- [ ] S8-F1-C2 — Create collapsible header widgets (MiMo)
- [ ] S8-F1-C3 — Replace bracketed text with colorful group badges (DeepSeek)

## Sprint 9 — Liquid Glass Aesthetic Upgrade

- [ ] S9-F1-C1 — Add glow/shadow effects (MiMo)
- [ ] S9-F1-C2 — Create SVG icon generators (MiMo)
- [ ] S9-F1-C3 — Apply icons to toolbar buttons (DeepSeek)
- [ ] S9-F1-C4 — Cache rendered icons (DeepSeek)

## Sprint 10 — Information Density (Visual Cards)

- [ ] S10-F1-C1 — Create SettingsCardWidget (MiMo)
- [ ] S10-F1-C2 — Group General tab settings (DeepSeek)

## Sprint 11 — Crash Report Client

- [ ] S11-F1-C1 — Redesign crash dialog UI (MiMo)
- [ ] S11-F1-C2 — Add Restart and Send Report buttons (DeepSeek)
- [ ] S11-F1-C3 — Add Technical Details drawer (MiMo)

## Sprint 12 — Hover Glow Animation

- [ ] S12-F1-C1 — Create GlassShineEffect (MiMo)
- [ ] S12-F1-C2 — Apply effect to main tasks panel (DeepSeek)
- [ ] S12-F1-C3 — Make effect optional (DeepSeek)

---

## Summary

- **Total sprints:** 12
- **Total chunks:** 35
- **MiMo chunks:** 18 (S1-F1-C1, S3-F1-C1, S4-F4-C1, S4-F4-C3, S5-F1-C1, S5-F1-C3, S6-F1-C3, S7-F1-C1, S7-F1-C2, S7-F1-C3, S8-F1-C1, S8-F1-C2, S9-F1-C1, S9-F1-C2, S10-F1-C1, S11-F1-C1, S11-F1-C3, S12-F1-C1)
- **DeepSeek chunks:** 17 (all others)
- **Critical path:** S7 → S9 → S12 (Settings Modernization → Liquid Glass → Hover Glow)
- **Parallelizable waves:** S5, S6, S7, S8, S11 (Phase 5 Wave 1)
