# Batch Bug Fix — Completion Checklist

**Batch:** batch-2026-06-20
**Date:** 2026-06-20

---

## Sprint 1 — High Severity

### S1-F1: Countdown Timer Visibility
- [ ] S1-F1-C1: Root cause confirmed (reminder setters don't notify widget)
- [ ] S1-F1-C2: Fix implemented (3 `set_task_ref` calls added)
- [ ] S1-F1-C3: Verification passed
- [ ] MiMo re-validation: ___

### S1-F2: Tray Icon Platform Fix
- [ ] S1-F2-C1: Root cause diagnosed
- [ ] S1-F2-C2: Fix implemented
- [ ] S1-F2-C3: Verification passed
- [ ] MiMo re-validation: ___

---

## Sprint 2 — Medium Severity

### S2-F1: Undo Toast Positioning
- [ ] S2-F1-C1: Smart positioning implemented
- [ ] S2-F1-C2: Edge cases verified

### S2-F2: Task Restore Position
- [ ] S2-F2-C1: Data flow designed
- [ ] S2-F2-C2: Implementation complete
- [ ] S2-F2-C3: Groups verified

### S2-F3: Dialog Shortcut Toggle
- [ ] S2-F3-C1: GlassPanelDialog.closeEvent added
- [ ] S2-F3-C2: All dialogs verified

---

## Sprint 3 — Low Severity

### S3-F1: Update Dialog Auto-Resize
- [ ] S3-F1-C1: adjustSize() added

### S3-F2: Native Export File Dialog
- [ ] S3-F2-C1: DontUseNativeDialog removed

---

## Final Verification

- [ ] All High severity fixes re-validated by MiMo
- [ ] No regressions in existing functionality
- [ ] Version bumped (if applicable)
- [ ] CHANGELOG updated (if applicable)
