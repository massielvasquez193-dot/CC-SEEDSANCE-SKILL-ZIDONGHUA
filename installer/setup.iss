; TikTok AI Factory Pro — Inno Setup Installer Script
; Build: Download Inno Setup (https://jrsoftware.org/isinfo.php) → Open this file → Compile

[Setup]
AppName=TikTok AI Factory Pro
AppVersion=3.0.0
AppPublisher=TikTok AI Factory
AppPublisherURL=https://github.com/massielvasquez193-dot/CC-SEEDSANCE-SKILL-ZIDONGHUA
DefaultDirName={autopf}\TikTok-AI-Factory-Pro
DefaultGroupName=TikTok AI Factory Pro
OutputDir=.\output
OutputBaseFilename=TikTok-AI-Factory-Pro-Setup-v3.0.0
SetupIconFile=..\installer\factory.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; Main project files
Source: "..\run_factory.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\version.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

; Source code
Source: "..\app\*.py"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs
Source: "..\agents\*.py"; DestDir: "{app}\agents"; Flags: ignoreversion recursesubdirs
Source: "..\providers\*.py"; DestDir: "{app}\providers"; Flags: ignoreversion recursesubdirs
Source: "..\prompts\*.py"; DestDir: "{app}\prompts"; Flags: ignoreversion recursesubdirs
Source: "..\skills\*.py"; DestDir: "{app}\skills"; Flags: ignoreversion recursesubdirs
Source: "..\workflows\*.py"; DestDir: "{app}\workflows"; Flags: ignoreversion recursesubdirs
Source: "..\config\*.py"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs
Source: "..\config\*.json"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs
Source: "..\license\*.py"; DestDir: "{app}\license"; Flags: ignoreversion recursesubdirs

; Start scripts
Source: "..\start\*.bat"; DestDir: "{app}\start"; Flags: ignoreversion
Source: "..\install\*.bat"; DestDir: "{app}\install"; Flags: ignoreversion

; Sample files
Source: "..\sample_input\*"; DestDir: "{app}\sample_input"; Flags: ignoreversion

; Empty directories
[Dirs]
Name: "{app}\input\products"
Name: "{app}\input\reference_videos"
Name: "{app}\input\characters"
Name: "{app}\output"
Name: "{app}\logs"

[Icons]
Name: "{group}\TikTok AI Factory Pro"; Filename: "{app}\start\启动工厂.bat"; WorkingDir: "{app}"
Name: "{group}\Watch Mode"; Filename: "{app}\start\启动监控模式.bat"; WorkingDir: "{app}"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"
Name: "{autodesktop}\TikTok AI Factory Pro"; Filename: "{app}\start\启动工厂.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\install\01_安装依赖.bat"; Description: "Install dependencies now"; Flags: postinstall nowait shellexec

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create .env if not exists
    if not FileExists(ExpandConstant('{app}\.env')) then
      FileCopy(ExpandConstant('{app}\.env.example'), ExpandConstant('{app}\.env'), False);
  end;
end;
