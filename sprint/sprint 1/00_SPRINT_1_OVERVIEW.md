# Sprint 1 — Auto-Update Feature

**Goal:** Implement complete auto-update system: check at startup, manual check button, download + install via PowerShell, Liquid Glass dialog.

**Prerequisites (do first, outside OpenCode):**
- [ ] Push current code to GitHub repo `user/nudge`
- [ ] Build `dist\Nudge\Nudge.exe` with `pyinstaller Nudge.spec`
- [ ] Create GitHub Release `v1.1.1` with the `.exe` as asset (current version is `1.1.0`)
- [ ] Note the release URL pattern: `https://api.github.com/repos/user/nudge/releases/latest`

**Tasks (in order):**

| Step | File | Description |
|------|------|-------------|
| 1 | `U1_updater_backend.md` | Create `src/backend/updater.py` — version check, download, PS installer |
| 2 | `U2_update_dialog.md` | Create `src/frontend/update_dialog.py` — Liquid Glass update dialog |
| 3 | `U3_state_defaults.md` | Add `checkForUpdates` + `updateCheckUrl` to StateManager |
| 4 | `U4_settings_checkbox.md` | Settings checkbox "Check for updates at startup" in General tab |
| 5 | `U5_chrome_button_boot.md` | Chrome ↻ button + `_check_and_prompt_update()` + boot timer |
| 6 | `U6_integration_test.md` | Build, upload to GitHub Release v1.0.2, test end-to-end |

**Dependencies:** Each step depends on previous. Confirm each before next.