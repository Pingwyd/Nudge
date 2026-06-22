# Sprint 3 — Low Severity Fixes

**Sprint:** S3
**Phase:** 3 (Low Severity)
**Duration:** 0.5 day
**Bugs:** B1 (update dialog clipping), B6 (export file dialog)

---

## Features

### S3-F1: Update Dialog Auto-Resize
**Bug:** B1 — Error text gets clipped in update dialog
**Root cause:** Missing `adjustSize()` after showing error text

### S3-F2: Native Export File Dialog
**Bug:** B6 — Export uses Qt themed dialog instead of native Windows Explorer
**Root cause:** `DontUseNativeDialog` flag forced in `QFileDialog.getSaveFileName`

---

## Chunks

| Chunk | Feature | Model | Type | Depends on |
|-------|---------|-------|------|-----------|
| S3-F1-C1 | Add adjustSize to DownloadDialog | DeepSeek V4 Flash | Pure-Logic | none |
| S3-F2-C1 | Remove DontUseNativeDialog flag | DeepSeek V4 Flash | Pure-Logic | none |

---

## Sequencing Map

```
S3-F1-C1 (parallel) S3-F2-C1
```

Both are independent single-line fixes. No verification chunks needed for Low severity.

---

## Checkpoint Questions

After S3:
- [ ] Does the update dialog resize to show full error text?
- [ ] Does the export file dialog show native Windows Explorer view?
