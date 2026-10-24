#define AppName "K86 Display Studio"
#define AppPublisher "CodeNotch"
#define AppId "{{812D989B-BE52-47F1-85D1-7A5D2B0A4A08}}"
#ifndef K86_VERSION
  #define K86_VERSION "1.0.0"
#endif

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#K86_VERSION}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\K86 Display Studio
DefaultGroupName={#AppName}
OutputDir=..\dist
OutputBaseFilename=K86DisplayStudio-{#K86_VERSION}-Windows-x64-Setup
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\K86 Display Studio.exe

[Files]
Source: "..\dist\K86 Display Studio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\K86 Display Studio.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\K86 Display Studio.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"

[Run]
Filename: "{app}\K86 Display Studio.exe"; Description: "Abrir {#AppName}"; Flags: postinstall nowait skipifsilent
