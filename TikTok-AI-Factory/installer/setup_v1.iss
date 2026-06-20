; TikTok AI Factory Pro v1.0 — Inno Setup Installer
; =====================================================
; Build: Install Inno Setup 6+ → Open this file → Compile
; Output: installer/output/TikTok-AI-Factory-Pro-v1.0-Setup.exe
;
; Prerequisites:
;   1. Run pyinstaller installer/launcher.spec first (generates dist/launcher.exe)
;   2. Open this file in Inno Setup Compiler
;   3. Click Compile

[Setup]
AppName=TikTok AI Factory Pro
AppVersion=1.0.0
AppPublisher=TikTok AI Factory
AppPublisherURL=https://tiktok-ai-factory.com
AppSupportURL=https://tiktok-ai-factory.com/support
DefaultDirName={autopf}\TikTok-AI-Factory-Pro
DefaultGroupName=TikTok AI Factory Pro
OutputDir=.\output
OutputBaseFilename=TikTok-AI-Factory-Pro-v1.0-Setup
SetupIconFile=..\installer\factory.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableProgramGroupPage=yes
UninstallDisplayName=TikTok AI Factory Pro v1.0.0
UninstallDisplayIcon={app}\launcher.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"

[Files]
; === Launcher executable (built by PyInstaller) ===
Source: "..\dist\launcher.exe"; DestDir: "{app}"; Flags: ignoreversion

; === Runtime Python files ===
Source: "..\release\client\*.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\release\client\*.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\release\client\*.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\release\client\.env.example"; DestDir: "{app}"; Flags: ignoreversion

; === Core packages ===
Source: "..\release\client\agents\*.py"; DestDir: "{app}\agents"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\app\*.py"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\app\gui\*.py"; DestDir: "{app}\app\gui"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\providers\*.py"; DestDir: "{app}\providers"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\config\*.py"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\config\*.json"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\license\*.py"; DestDir: "{app}\license"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\updater\*.py"; DestDir: "{app}\updater"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\workflows\*.py"; DestDir: "{app}\workflows"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\skills\*.py"; DestDir: "{app}\skills"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\prompts\*.py"; DestDir: "{app}\prompts"; Flags: ignoreversion recursesubdirs
Source: "..\release\client\tools\*.py"; DestDir: "{app}\tools"; Flags: ignoreversion recursesubdirs

; === Case Library ===
Source: "..\release\client\case_library\*"; DestDir: "{app}\case_library"; Flags: ignoreversion recursesubdirs

; === Installer scripts (for dependency setup) ===
Source: "install_deps.bat"; DestDir: "{app}\installer"; Flags: ignoreversion

[Files]
; === Create .env from template if not exists ===
Source: "..\release\client\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist

[Dirs]
; Auto-create empty runtime directories
Name: "{app}\input\products"
Name: "{app}\input\characters"
Name: "{app}\input\reference_videos"
Name: "{app}\output"
Name: "{app}\logs"

[Icons]
Name: "{group}\TikTok AI Factory Pro"; Filename: "{app}\launcher.exe"; WorkingDir: "{app}"
Name: "{group}\卸载 TikTok AI Factory Pro"; Filename: "{uninstallexe}"
Name: "{autodesktop}\TikTok AI Factory Pro"; Filename: "{app}\launcher.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\launcher.exe"; Description: "启动 TikTok AI Factory Pro"; Flags: postinstall nowait skipifsilent shellexec

[UninstallRun]
; Cleanup on uninstall (preserve user data prompt)
Filename: "cmd.exe"; Parameters: "/c echo User data in output/ and logs/ will be preserved."; Flags: runhidden

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Ensure .env exists
    if not FileExists(ExpandConstant('{app}\.env')) then
      FileCopy(ExpandConstant('{app}\.env.example'), ExpandConstant('{app}\.env'), False);
  end;
end;

// Ask user about preserving data on uninstall
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    if DirExists(ExpandConstant('{app}\output')) then
      MsgBox('output/ 和 logs/ 目录中的用户数据将被保留。' + #13#10 +
             '如需完全删除，请手动删除安装目录。', mbInformation, MB_OK);
  end;
end;
