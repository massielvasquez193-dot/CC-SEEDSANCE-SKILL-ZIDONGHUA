@echo off
chcp 65001 >nul
title TikTok AI Factory Pro — 安装依赖

echo ============================================================
echo   TikTok AI Factory Pro — 依赖安装
echo ============================================================
echo.

echo [1/5] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [OK] Python 已就绪

echo.
echo [2/5] 升级 pip...
python -m pip install --upgrade pip -q

echo.
echo [3/5] 安装核心依赖...
pip install -r ..\requirements.txt -q

echo.
echo [4/5] 安装可选依赖...
pip install Pillow opencv-python -q
pip install openai anthropic google-generativeai -q
pip install python-dotenv watchdog -q

echo.
echo [5/5] 检查 ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未检测到 ffmpeg，视频分析功能将受限
    echo 下载地址: https://ffmpeg.org/download.html
) else (
    echo [OK] ffmpeg 已就绪
)

echo.
echo ============================================================
echo   安装完成！请执行下一步: 02_检测环境.bat
echo ============================================================
pause
