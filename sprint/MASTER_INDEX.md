# Nudge — Master Execution Plan

## Repository Structure
```
sprint/
├── sprint 1/          Auto-Update Feature (6 tasks)
│   ├── 00_SPRINT_1_OVERVIEW.md
│   ├── U1_updater_backend.md
│   ├── U2_update_dialog.md
│   ├── U3_state_defaults.md
│   ├── U4_settings_checkbox.md
│   ├── U5_chrome_button_boot.md
│   └── U6_integration_test.md
│
├── sprint 2/          Critical Bug Fixes (8 tasks)
│   ├── 00_SPRINT_2_OVERVIEW.md
│   ├── B1_tray_icon.md
│   ├── B2_text_clip_min_width.md
│   ├── B3_edit_mode_clipping.md
│   ├── B4_always_on_top_text_loss.md
│   ├── B5_dark_theme_reapply.md
│   ├── B6_remove_checkboxes.md
│   ├── B7_min_width_text_span.md
│   └── B8_close_confirmation.md
│
├── sprint 3/          UX Polish (7 tasks)
│   ├── 00_SPRINT_3_OVERVIEW.md
│   ├── P1_shortcut_toggle.md
│   ├── P2_text_size_all.md
│   ├── P3_text_size_preview.md
│   ├── P4_incremental_list.md
│   ├── P5_settings_5tab.md
│   ├── P6_locked_groups.md
│   └── P7_double_esc_config.md
│
├── sprint 4/          Backlog Verification (7 items)
│   ├── 00_SPRINT_4_OVERVIEW.md
│   ├── R1_boot_icon_path.md
│   └── R2_R7_verification_bundle.md
│
└── sprint 5/          New Features (4 tasks)
    ├── 00_SPRINT_5_OVERVIEW.md
    ├── N1_tutorial_changelog.md
    ├── N2_buy_me_a_coffee.md
    ├── N3_code_signing.md
    └── N4_friendly_changelog.md
```

## Execution Order

```
Phase 1: Auto-Update     → Sprint 1 (U1 → U2 → U3 → U4 → U5 → U6)
Phase 2: Critical Fixes  → Sprint 2 (B1 → B2/B7 → B3 → B4 → B5 → B6 → B8)
Phase 3: UX Polish       → Sprint 3 (P1 → P2/P3 → P4 → P5 → P6 → P7)
Phase 4: Verify Backlog  → Sprint 4 (R1 → R2-R7 bundle)
Phase 5: New Features    → Sprint 5 (N1 → N2 → N3 → N4)
```

## How to Use
1. Open `sprint/{n}/00_SPRINT_N_OVERVIEW.md` for the sprint overview
2. Feed each `.md` prompt file into OpenCode one at a time
3. Confirm each step completes before moving to the next
4. Tasks within a sprint can be parallelized if they don't share files

## Version Reference
| Version | Status |
|---------|--------|
| 1.1.0 | Current (src/__init__.py) |
| 1.1.1 | Next release (target for Sprint 1) |

## Key Principles for All Prompts
- **Read before edit** — always read file first
- **Minimal changes** — never refactor unrelated code
- **Industry best practices** — clean code, single responsibility, proper error handling
- **Efficient** — no redundant operations, no unnecessary allocations
- **Thread-safe** — network in background threads, UI on main thread
- **Theme-consistent** — use theme.py tokens, not hardcoded colors