[Setup]
define MyAppName "LLBatchDispatch"
define MyAppVersion "0.9"
define MyAppPublisher "Dragonwire and LasagnaLove"
define MyAppURL "https://www.lasagnalove.org"
define MyAppExeName "BatchDispatch.exe"
#define MyAppName "LLBatchDispatch"


; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{27C561EB-11D3-4795-A2CF-32D14EA721CB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
# ; "ArchitecturesAllowed=x64compatible" specifies that Setup cannot run
# ; on anything but x64 and Windows 11 on Arm.
ArchitecturesAllowed=x64compatible
# ; "ArchitecturesInstallIn64BitMode=x64compatible" requests that the
# ; install be done in "64-bit mode" on x64 or Windows 11 on Arm,
# ; meaning it should use the native 64-bit Program Files directory and
# ; the 64-bit view of the registry.
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
# ; Uncomment the following line to run in non administrative install mode (install for current user only).
# ;PrivilegesRequired=lowest

DefaultGroupName=BatchDispatch
OutputDir=Output
OutputBaseFilename=BatchDispatch_Setup
Compression=lzma
SolidCompression=yes


[Files]
; The executable created by PyInstaller
Source: "dist\BatchDispatch.exe"; DestDir: "{app}"; Flags: ignoreversion
; Bundling the templates into a subfolder for the app to find on first run
Source: "resources\templates\default_standard.txt"; DestDir: "{app}\resources\templates"; Flags: ignoreversion
Source: "resources\templates\diet_allergy.txt"; DestDir: "{app}\resources\templates"; Flags: ignoreversion

[Icons]
Name: "{group}\BatchDispatch"; Filename: "{app}\BatchDispatch.exe"
Name: "{commondesktop}\BatchDispatch"; Filename: "{app}\BatchDispatch.exe"
