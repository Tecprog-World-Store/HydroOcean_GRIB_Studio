#define MyAppName "HydroOcean GRIB Studio"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "Tecprog World E.I.R.L."
#define MyAppExeName "HydroOceanGRIBStudio.exe"

[Setup]
AppId={{B7B10CC1-4AB9-4B2B-8CA9-7BBA2EA71A20}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Tecprog World\HydroOcean GRIB Studio
DefaultGroupName=Tecprog World
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=HydroOceanGRIBStudio_Setup_v0.2.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#MyAppName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "..\dist\HydroOceanGRIBStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName}"; Flags: nowait postinstall skipifsilent
