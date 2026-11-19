; Inno Setup 6 script for the Windows installer of SQRM8 (per-user, no admin rights).
;
;   ISCC.exe /DAppVersion=0.3.0 /DArch=x64 /DDistDir=..\..\dist\SQRM8 /DOutputDir=..\..\dist\installer ^
;            packaging\windows\installer.iss
;
; Relative paths are relative to this file. Output: SQRM8-<version>-windows-<arch>.exe
; The release workflow passes the version from host/companion/version.py (packaging/check_version.py).

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef Arch
  #define Arch "x64"
#endif
#ifndef DistDir
  #define DistDir "..\..\dist\SQRM8"
#endif
#ifndef OutputDir
  #define OutputDir "..\..\dist\installer"
#endif
; "x64compatible" (x64 Windows and Windows 11 on Arm with x64 emulation) needs Inno Setup 6.3+; older 6.x
; compilers only know "x64".
#if Ver >= EncodeVer(6, 3, 0)
  #define ArchAllowed "x64compatible"
#else
  #define ArchAllowed "x64"
#endif
#define AppName "SQRM8"
#define AppExe "SQRM8.exe"
; The app was called "Claudius Maximus" up to 0.7.x: a different AppId, folder, exe and Run value. [Code] below
; removes such an install before this one goes in (see PrepareToInstall).
#define LegacyAppId "{6F1B7E2A-4C1D-4E7B-9C55-2D3A8B0C9E41}"
#define LegacyExe "ClaudiusMaximus.exe"
#define LegacyName "Claudius Maximus"
#define LegacyRunValue "ClaudiusMaximus"

[Setup]
; Never change the AppId: it identifies the installation for upgrades and the uninstaller. (It changed once, with
; the rename to SQRM8 in 0.8.0; LegacyAppId is the old one.)
AppId={{4CB82B19-5444-48A4-A5D9-DB6BC97B720C}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=SQRM8
AppPublisherURL=https://github.com/d-weber/SQRM8
AppSupportURL=https://github.com/d-weber/SQRM8/issues
VersionInfoVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\SQRM8
DisableDirPage=auto
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed={#ArchAllowed}
ArchitecturesInstallIn64BitMode={#ArchAllowed}
OutputDir={#OutputDir}
OutputBaseFilename=SQRM8-{#AppVersion}-windows-{#Arch}
SetupIconFile=..\icons\app.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Close the running tray app (it holds the exe and its _internal\*.pyd/.dll open) before replacing or removing
; files, via the Restart Manager; the [Run] entry starts the new version afterwards.
CloseApplications=force
CloseApplicationsFilter=*.exe,*.dll,*.pyd
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "autostart"; Description: "Start {#AppName} when I log in"; GroupDescription: "Startup:"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; Parameters: "app"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Parameters: "app"; Tasks: desktopicon

[Registry]
; Same value as companion/autostart.py writes, so the tray's "Start at login" toggle and the installer agree.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "SQRM8"; \
  ValueData: """{app}\{#AppExe}"" app"; Flags: uninsdeletevalue; Tasks: autostart
; Unconditional: also remove the value at uninstall when "Start at login" was turned on later from the tray menu
; (ValueType none writes nothing at install time).
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "SQRM8"; \
  Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#AppExe}"; Parameters: "app"; Description: "{cm:LaunchProgram,{#AppName}}"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove our hooks and statusLine wrapper from ~/.claude/settings.json while the exe is still there,
; then make sure no copy of the app keeps files open.
Filename: "{app}\{#AppExe}"; Parameters: "hooks uninstall"; Flags: runhidden waituntilterminated; RunOnceId: "HooksUninstall"
Filename: "{sys}\taskkill.exe"; Parameters: "/F /T /IM {#AppExe}"; Flags: runhidden waituntilterminated; RunOnceId: "KillApp"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
const
  LegacyUninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#LegacyAppId}_is1';
  RunKey = 'Software\Microsoft\Windows\CurrentVersion\Run';

{ Replace a "Claudius Maximus" (<= 0.7.x) install by hand instead of running its uninstaller: that one runs
  "ClaudiusMaximus.exe hooks uninstall", which strips the user's Claude Code hooks and statusLine wrapper (and
  their choice of them). Left in place, those hooks point at the old exe; the new app rewrites them to itself on
  its first start (companion.app _refresh_stale_hooks), and moves ~/.claudius-maximus to ~/.sqrm8. }
procedure RemoveLegacyInstall;
var
  Dir: String;
  RC: Integer;
begin
  if not RegKeyExists(HKCU, LegacyUninstallKey) then
    Exit;
  if not RegQueryStringValue(HKCU, LegacyUninstallKey, 'InstallLocation', Dir) then
    Dir := ExpandConstant('{localappdata}\Programs\ClaudiusMaximus');
  Dir := RemoveBackslashUnlessRoot(Dir);
  Log('Replacing the {#LegacyName} install in ' + Dir);
  { the old tray app holds its exe and _internal\ files open, and it owns the device }
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM {#LegacyExe}', '', SW_HIDE, ewWaitUntilTerminated, RC);
  Sleep(1000);
  { only a folder that really holds the old app is deleted, never whatever InstallLocation might say }
  if FileExists(AddBackslash(Dir) + '{#LegacyExe}') then
    DelTree(Dir, True, True, True);
  RegDeleteValue(HKCU, RunKey, '{#LegacyRunValue}');
  DeleteFile(ExpandConstant('{autoprograms}\{#LegacyName}.lnk'));
  DeleteFile(ExpandConstant('{autodesktop}\{#LegacyName}.lnk'));
  { keep the Apps & features entry if the folder could not be removed, so the user can still uninstall it }
  if not DirExists(Dir) then
    RegDeleteKeyIncludingSubkeys(HKCU, LegacyUninstallKey)
  else
    Log('could not remove ' + Dir + ': keeping its uninstall entry');
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  RemoveLegacyInstall;
  Result := '';
end;
