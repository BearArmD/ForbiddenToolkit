#define MyAppName "ForbiddenToolkit"
#define MyAppVersion "1.0"
#define MyAppPublisher "Forbidden Cheese Development"
#define MyAppURL "https://github.com/BearArmD"
#define MyAppExeName "ForbiddenToolkit.exe"
#define SourceDir "D:\Forbid_Files\ForbiddenToolkit"

[Setup]
AppId={{FC-TOOLKIT-V1-2026}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\ForbiddenToolkit
DefaultGroupName=Forbidden Cheese Development
OutputDir={#SourceDir}\Output
OutputBaseFilename=ForbiddenToolkit_Setup_v1
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Main executable
Source: "{#SourceDir}\ForbiddenToolkit.exe";   DestDir: "{app}"; Flags: ignoreversion

; Branding and splash
Source: "{#SourceDir}\ForbidLogo2.png";         DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\SplashVideo.mp4";          DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\SplashSound.wav";          DestDir: "{app}"; Flags: ignoreversion

; Audio files
Source: "{#SourceDir}\BGM.wav";                  DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\welcome.wav";              DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\results.wav";              DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\nomatch.wav";              DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\error.wav";                DestDir: "{app}"; Flags: ignoreversion

; ExifTool -- full folder with dependencies
Source: "{#SourceDir}\ExifTool\*"; DestDir: "{app}\ExifTool"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ForbiddenToolkit";        Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall ForbiddenToolkit"; Filename: "{uninstallexe}"
Name: "{userdesktop}\ForbiddenToolkit"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure WriteConfig();
var
  AppPath: String;
  ConfigPath: String;
  Lines: TArrayOfString;
begin
  AppPath   := ExpandConstant('{app}');
  ConfigPath := AppPath + '\fk_config.ini';

  SetArrayLength(Lines, 14);
  Lines[0]  := '[paths]';
  Lines[1]  := 'logo_path = '    + AppPath + '\ForbidLogo2.png';
  Lines[2]  := 'splash_video = ' + AppPath + '\SplashVideo.mp4';
  Lines[3]  := 'splash_audio = ' + AppPath + '\SplashSound.wav';
  Lines[4]  := 'exiftool = '     + AppPath + '\ExifTool\ExifTool.exe';
  Lines[5]  := 'bgm_wav = '      + AppPath + '\BGM.wav';
  Lines[6]  := 'welcome_wav = '  + AppPath + '\welcome.wav';
  Lines[7]  := 'results_wav = '  + AppPath + '\results.wav';
  Lines[8]  := 'nomatch_wav = '  + AppPath + '\nomatch.wav';
  Lines[9]  := 'error_wav = '    + AppPath + '\error.wav';
  Lines[10] := '';
  Lines[11] := '[state]';
  Lines[12] := 'first_run = True';
  Lines[13] := '';

  SaveStringsToFile(ConfigPath, Lines, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    WriteConfig();
end;
