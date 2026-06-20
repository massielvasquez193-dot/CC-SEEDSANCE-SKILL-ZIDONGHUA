@echo off
chcp 65001 >nul
title TikTok AI Factory Pro — Watch Mode 监控中...

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║   TikTok AI Factory Pro — Watch Mode 监控模式         ║
echo ╚══════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0.."

echo [监控中] 系统正在监控 input/ 目录...
echo.
echo   放入新文件 → 自动检测 → 自动生成视频 → output/
echo.
echo   input/products/          ← 放产品图片
echo   input/reference_videos/  ← 放参考视频
echo   input/characters/        ← 放人物图片
echo.
echo   按 Ctrl+C 停止监控
echo.

python run_factory.py --watch --interval 5

pause
