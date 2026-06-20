@echo off
chcp 65001 >nul
title TikTok AI Factory Pro — 环境检测

echo ============================================================
echo   TikTok AI Factory Pro — 环境检测
echo ============================================================
echo.

set OK=0
set WARN=0
set FAIL=0

echo [1/6] Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FAIL] Python 未安装
    set /a FAIL+=1
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo   [OK] Python %%v
    set /a OK+=1
)

echo.
echo [2/6] pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FAIL] pip 不可用
    set /a FAIL+=1
) else (
    echo   [OK] pip 已就绪
    set /a OK+=1
)

echo.
echo [3/6] ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARN] ffmpeg 未安装 (视频分析需要)
    set /a WARN+=1
) else (
    echo   [OK] ffmpeg 已就绪
    set /a OK+=1
)

echo.
echo [4/6] 输入目录...
if exist "..\input\products" (echo   [OK] input\products) else (echo   [WARN] input\products 不存在)
if exist "..\input\reference_videos" (echo   [OK] input\reference_videos) else (echo   [WARN] input\reference_videos 不存在)
if exist "..\input\characters" (echo   [OK] input\characters) else (echo   [WARN] input\characters 不存在)

echo.
echo [5/6] API 配置...
if exist "..\.env" (
    echo   [OK] .env 文件存在
    set /a OK+=1
) else (
    echo   [WARN] .env 文件不存在，请复制 .env.example 并填入API密钥
    set /a WARN+=1
)

echo.
echo [6/6] 端口/网络...
ping -n 1 api.openai.com >nul 2>&1 && echo   [OK] 网络连通 || echo   [WARN] 网络受限

echo.
echo ============================================================
echo   检测完成: OK=%OK%  WARN=%WARN%  FAIL=%FAIL%
echo ============================================================
if %FAIL% gtr 0 (
    echo [FAIL] 有 %FAIL% 个致命错误，请先解决。
)
if %WARN% gtr 0 (
    echo [WARN] 有 %WARN% 个警告，建议处理。
)
echo.
pause
