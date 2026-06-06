; Nudge — Inno Setup installer script
;
; Compiled by CI via:
;   ISCC.exe installer.iss /DMyAppVersion=1.0.0
;
; Output: Output\Nudge-Setup-{MyAppVersion}.exe

#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#ifndef MyAppExeName
  #define MyAppExeName "Nudge"
#endif

[Setup]
AppId={{B7E9A2D3-4C5F-6A7B-8C9D-0E1F2A3B4C5D}
AppName=Nudge
AppVersion={#MyAppVersion}
AppVerName=Nudge {#MyAppVersion}
AppPublisher=Nudge Contributors
AppPublisherURL=https://github.com/your-org/Nudge
AppSupportURL=https://github.com/your-org/Nudge/issues
AppUpdatesURL=https://github.com/your-org/Nudge/releases
DefaultDirName={autopf}\Nudge
DefaultGroupName=Nudge
DisableProgramGroupPage=yes
LicenseFile=LICENSE
InfoBeforeFile=README.md
OutputDir=Output
OutputBaseFilename=Nudge-Setup-{#MyAppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Uninstallable=yes
CloseApplicationsFilter=*.exe
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
BeveledLabel=Nudge — a liquid-glass task widget

[Files]
; Bundle the PyInstaller --onedir output verbatim.
Source: "dist\{#MyAppExeName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Include the license and readme in the install dir so the user can find them.
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Nudge"; Filename: "{app}\{#MyAppExeName}.exe"; IconFilename: "{app}\{#MyAppExeName}.exe"; Comment: "Open Nudge"
Name: "{group}\Uninstall Nudge"; Filename: "{uninstallexe}"; IconFilename: "{uninstallexe}"
Name: "{autodesktop}\Nudge"; Filename: "{app}\{#MyAppExeName}.exe"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}.exe"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}.exe"; Description: "{cm:LaunchProgram,Nudge}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; No cleanup needed — %APPDATA%\Nudge is preserved across uninstalls
; so the user's tasks, history, and settings survive a reinstall.
Filename: "{cmd}"; Parameters: "/C echo Nudge data files are kept in %APPDATA%\Nudge"; Flags: runmaximized; RunOnceId: "NudgeDataHint"

[UninstallDelete]
; Do NOT remove AppData on uninstall — the user might reinstall and want their data back.
