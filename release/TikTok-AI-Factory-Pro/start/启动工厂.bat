@echo off
chcp 65001 >nul
title TikTok AI Factory Pro — 运行中...

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║     TikTok AI Factory Pro — 全自动视频生产工厂        ║
echo ╚══════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0.."

echo [提示] 请确保已在 input/ 目录放入:
echo    - products/       产品图片
echo    - reference_videos/ 参考视频
echo    - characters/     人物图片
echo.
echo [提示] 请确保 .env 文件已配置 API 密钥
echo.

choice /c 12 /n /m "选择模式: [1] 全自动生产  [2] 单任务模式: "
if errorlevel 2 goto single
if errorlevel 1 goto auto

:auto
echo.
echo [启动] 全自动模式 — 扫描input/ → 自动生成所有视频
echo.
python run_factory.py
goto end

:single
echo.
echo [启动] 单任务模式 — 使用 sample_input/ 示例素材
echo.
if exist "sample_input\product.jpg" (
    python run_factory.py --mode single ^
        --product "sample_input/product.jpg" ^
        --video "sample_input/reference.mp4" ^
        --character "sample_input/character.jpg" ^
        --task-id demo_task
) else (
    echo [错误] sample_input/ 中缺少示例素材
    echo 请先将产品图/参考视频/人物图放入 input/ 目录
)
goto end

:end
echo.
echo ============================================================
echo   运行完成！查看 output/ 目录获取生成结果
echo ============================================================
pause
