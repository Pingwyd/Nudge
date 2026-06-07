# U6 — Integration Test & Release

## Prerequisites (Manual, before running this step)
- [ ] GitHub repo `user/nudge` exists and code is pushed
- [ ] `pyinstaller Nudge.spec` builds successfully
- [ ] `dist\Nudge\Nudge.exe` created

---

## Steps

### 1. Create GitHub Release v1.1.1
```bash
# From project root
gh release create v1.1.1 dist/Nudge/Nudge.exe --title "Nudge v1.1.1" --notes "Auto-update test release"
```
- Verify release appears at: `https://github.com/user/nudge/releases/tag/v1.1.1`
- Verify asset URL: `https://github.com/user/nudge/releases/download/v1.1.1/Nudge.exe`

### 2. Verify API Response
```bash
curl -H "Accept: application/json" https://api.github.com/repos/user/nudge/releases/latest
```
- Check `tag_name` = `"v1.1.1"`
- Check `assets[0].browser_download_url` points to `.exe`
- Check `body` contains changelog

### 3. Test Current Version (1.1.0) Detects Update
1. Run `dist\Nudge\Nudge.exe` (version 1.1.0)
2. Wait 3 seconds → Update dialog should appear
3. Verify dialog shows:
   - Title: "Update Available — Nudge v1.1.1"
   - Current: "Current version: 1.1.0"
   - Changelog from release body
4. Click "Remind Me Later" → dialog dismisses, app continues

### 4. Test Manual Check (Chrome Button)
1. Click ↻ button in title bar
2. Same dialog appears
3. Click "Download & Install"
4. "Downloading v1.1.1..." message shows
5. App closes
6. Wait ~3 seconds → App relaunches as v1.1.1

### 5. Verify New Version Running
- Check window title / About → shows 1.1.1
- Settings → "Check for updates at startup" still checked
- No immediate update dialog (same version)

### 6. Test Settings Toggle
1. Open Settings → General → Uncheck "Check for updates at startup"
2. Save → Close Settings
3. Restart app
4. Wait 10 seconds → No update check (no network call)
5. Re-enable → Restart → Check runs

### 7. Test Edge Cases
| Scenario | Expected |
|----------|----------|
| No internet | Silent fail, no crash, no dialog |
| Same version (1.1.1) | `available: false`, no dialog |
| Malformed JSON | Silent fail |
| Download interrupted | Warning dialog, app stays open |
| PowerShell blocked | Warning dialog, app stays open |

---

## Build Commands Reference
```bash
# Clean build
Remove-Item dist, build -Recurse -Force -ErrorAction SilentlyContinue
pyinstaller Nudge.spec

# Test built exe
.\dist\Nudge\Nudge.exe
```

---

## Rollback Plan
If v1.1.1 has issues:
1. Delete GitHub release `v1.1.1`
2. Fix code
3. Rebuild
4. Create new release `v1.1.2`

---

## Sign-Off Checklist
- [ ] Boot check works (3s delay)
- [ ] Manual check works (↻ button)
- [ ] Download + install completes
- [ ] App relaunches as new version
- [ ] Settings checkbox persists
- [ ] Settings checkbox controls boot check
- [ ] No crashes on network errors
- [ ] Dialog positioning avoids overlap
- [ ] Theme consistency (dark/light)