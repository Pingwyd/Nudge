# N3 — Code Signing & Microsoft SmartScreen Guide

## Overview
This is an **external process** — not code changes. Signing your .exe with an EV (Extended Validation) certificate removes SmartScreen warnings and builds user trust.

## Requirements
- **EV Code Signing Certificate:** ~$300-500/year from Sectigo, DigiCert, etc.
- **Hardware token:** Most EV certs require a USB token
- **Windows SDK:** `signtool.exe` comes with Windows SDK or Visual Studio

---

## Steps

### 1. Purchase EV Certificate
- Provider: DigiCert, Sectigo, SSL.com
- Verify your identity (company registration or individual ID)
- Receive hardware token with certificate

### 2. Sign the Executable
```bash
# After building with pyinstaller
signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 ^
    "dist\Nudge\Nudge.exe"
```

### 3. Verify Signature
```bash
signtool verify /pa "dist\Nudge\Nudge.exe"
# Should show: "Successfully verified"
```

### 4. Submit to Microsoft Defender
```bash
# Submit for SmartScreen reputation
signtool verify /pa /tw "dist\Nudge\Nudge.exe"
# Then submit via: https://www.microsoft.com/en-us/wdsi/filesubmission
```

### 5. Automate in Build Pipeline
Add to `Nudge.spec` post-build step or create a `build_and_sign.bat`:

```batch
@echo off
pyinstaller Nudge.spec
signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 dist\Nudge\Nudge.exe
echo Signed successfully
```

## Verification
- Right-click .exe → Properties → Digital Signatures tab → signature present
- No SmartScreen warning on download (after reputation built)
- Windows Defender doesn't flag as unknown

## Estimated Timeline
- Certificate issuance: 1-5 business days
- SmartScreen reputation: 1-4 weeks (depending on downloads)
- Total: ~2-5 weeks

## Alternative (Free)
If you don't want to pay for a certificate:
1. Build user trust through GitHub releases
2. Users will see "Windows protected your PC" initially
3. After enough downloads (1000+ installs), Microsoft auto-builds reputation
4. Provide instructions: "Click 'More info' → 'Run anyway'"