# Sprint 2 — Critical Bug Fixes

**Goal:** Fix 8 critical bugs affecting core UX: tray integration, text clipping, theme regression, always-on-top issues, redundant checkboxes.

**Priority:** HIGH — These block daily usability.

| Step | File | Description |
|------|------|-------------|
| 1 | `B1_tray_icon.md` | System tray icon + minimize-to-tray + right-click menu |
| 2 | `B2_text_clip_min_width.md` | Fix text clipped at minimum width on first insert |
| 3 | `B3_edit_mode_clipping.md` | Fix task text clipping when editing |
| 4 | `B4_always_on_top_text_loss.md` | Fix text disappearing when enabling Always-on-top |
| 5 | `B5_dark_theme_reapply.md` | Fix dark theme not fully applying when switching from light |
| 6 | `B6_remove_checkboxes.md` | Remove checkboxes (click task = send to history) |
| 7 | `B7_min_width_text_span.md` | Text column spans to Edit button at minimum width |
| 8 | `B8_close_confirmation.md` | Confirmation dialog on close (with tray option) |

**Dependencies:** B1 must complete before B8 (B8 needs tray). B2, B3, B7 are related (text layout).