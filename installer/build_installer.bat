@echo off
chcp 65001 >nul
title TikTok AI Factory Pro — Build Installer

echo ============================================================
echo   TikTok AI Factory Pro — Windows Installer Builder
echo ============================================================
echo.

cd /d "%~dp0.."

echo [选择构建方式]
echo.
echo   [1] Inno Setup (.exe installer) — 推荐
echo   [2] PyInstaller (.exe self-extracting)
echo   [3] NSIS (.exe installer)
echo.
choice /c 123 /n /m "请选择: "

if errorlevel 3 goto nsis
if errorlevel 2 goto pyinstaller
if errorlevel 1 goto inno

:inno
echo.
echo === 构建 Inno Setup 安装包 ===
echo.
echo 需要: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
echo.
where iscc >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Inno Setup Compiler (iscc.exe) 未找到
    echo 请安装 Inno Setup 并添加到 PATH
    pause
    exit /b 1
)
echo [OK] Inno Setup Compiler 已找到
echo.
echo 正在编译 installer\setup.iss ...
iscc installer\setup.iss
if %errorlevel% equ 0 (
    echo.
    echo [OK] 安装包已生成: installer\output\TikTok-AI-Factory-Pro-Setup-v3.0.0.exe
) else (
    echo [FAIL] 编译失败
)
goto end

:pyinstaller
echo.
echo === 构建 PyInstaller 自解压安装包 ===
echo.
pip install pyinstaller -q 2>nul
echo [OK] PyInstaller 已安装
echo.
echo 正在编译 installer\setup_script.py → Setup.exe ...
pyinstaller --onefile --windowed --name "TikTok-AI-Factory-Pro-Setup" ^
    --add-data "start;start" ^
    --add-data "install;install" ^
    --add-data ".env.example;." ^
    --add-data "requirements.txt;." ^
    installer\setup_script.py
if %errorlevel% equ 0 (
    echo [OK] Setup.exe 已生成: dist\TikTok-AI-Factory-Pro-Setup.exe
) else (
    echo [FAIL] 编译失败
)
goto end

:nsis
echo.
echo === 构建 NSIS 安装包 ===
echo.
echo 需要: NSIS 3+ (https://nsis.sourceforge.io/)
echo.
where makensis >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] NSIS (makensis.exe) 未找到
    pause
    exit /b 1
)
echo [OK] NSIS 已找到
echo 正在编译 install.nsi ...
makensis installer\install.nsi
echo.
echo [OK] 安装包已生成
goto end

:end
echo.
echo ============================================================
echo   构建完成
echo ============================================================
pause
