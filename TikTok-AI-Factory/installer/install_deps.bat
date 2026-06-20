@echo off
chcp 65001 >nul
title TikTok AI Factory Pro — Installing Dependencies

echo ============================================================
echo   TikTok AI Factory Pro — Dependency Setup
echo ============================================================
echo.

echo [1/3] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
python --version
echo.

echo [2/3] Installing pip packages...
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt
echo.

echo [3/3] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] FFmpeg not found.
    echo Video composition requires FFmpeg.
    echo Install: winget install Gyan.FFmpeg
) else (
    echo [OK] FFmpeg found
)
echo.

echo ============================================================
echo   Setup complete! Run launcher.exe to start.
echo ============================================================
pause
