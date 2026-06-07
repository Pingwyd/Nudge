# Nudge — MASTER INDEX

## Execution Order (feed into OpenCode in this sequence)

```
Phase 0: Foundation
   ├── 0.1_read_all_sources.md
   └── 0.2_verify_imports.md

Phase 1: Critical Bug Fixes
   ├── 1.1_text_clipped_min_width_insert.md
   ├── 1.2_text_3_columns_min_width.md
   ├── 1.3_text_clipping_bottom_edit.md
   ├── 1.4_dark_theme_system_wide.md
   └── 1.5_aot_task_add_text_loss.md

Phase 5: New Features
   ├── 5.1_tutorial_whatsnew.md
   ├── 5.2_flutterwave_donate.md
   └── 5.3_friendly_changelog.md

Phase 6: App Optimization
   ├── 6.1_pyinstaller_audit.md
   ├── 6.2_lazy_imports.md
   ├── 6.3_resource_optimization.md
   ├── 6.4_render_performance.md
   └── 6.5_memory_profiling.md

Phase 7: Backlog Verification
   └── 7.1_verification_bundle.md
```

## Key Principles (for all prompts)
- Read file before editing
- Minimal changes, never refactor unrelated code
- Use theme.py tokens, never hardcoded colors
- Thread-safe: network/disk I/O off main thread
- Test both dark and light themes after each change