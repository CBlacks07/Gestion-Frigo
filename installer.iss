; Script Inno Setup pour Gestion-Frigo

#define MyAppName "Gestion-Frigo"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Gestion-Frigo"
#define MyAppExeName "Gestion-Frigo.exe"

[Setup]
; Informations de base
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Fichier de sortie
OutputDir=installer_output
OutputBaseFilename=Gestion-Frigo-Setup
; Icône et compression
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Privilèges
PrivilegesRequired=admin

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Créer une icône dans la barre de lancement rapide"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\Gestion-Frigo.exe"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: N'utilisez pas "Flags: ignoreversion" sur les fichiers système

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
