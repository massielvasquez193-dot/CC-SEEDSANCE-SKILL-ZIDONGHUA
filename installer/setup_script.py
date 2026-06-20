"""
TikTok AI Factory Pro — Windows Installer
===========================================
双击运行 → 自动检测环境 → 安装依赖 → 创建快捷方式

可编译为 Setup.exe: pyinstaller --onefile --windowed setup_script.py
"""

import os
import sys
import subprocess
import shutil
import urllib.request
import tempfile
import ctypes
from pathlib import Path


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)


def print_step(n, total, msg):
    print(f"\n{'='*60}")
    print(f"  [{n}/{total}] {msg}")
    print(f"{'='*60}")


def check_python():
    print_step(1, 7, "检测 Python 环境")
    try:
        result = subprocess.run(
            ["python", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            ver = result.stdout.strip()
            print(f"  [OK] {ver} 已安装")
            return True
    except Exception:
        pass

    print("  [INSTALL] Python 未检测到，正在自动安装...")
    try:
        url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        tmp = Path(tempfile.gettempdir()) / "python_installer.exe"
        print(f"  下载: {url}")
        urllib.request.urlretrieve(url, tmp)
        print("  安装中 (静默模式)...")
        subprocess.run(
            [str(tmp), "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0"],
            timeout=300,
        )
        tmp.unlink()
        print("  [OK] Python 安装完成")
        return True
    except Exception as e:
        print(f"  [FAIL] 自动安装失败: {e}")
        print("  请手动安装: https://www.python.org/downloads/")
        return False


def install_requirements():
    print_step(2, 7, "安装 Python 依赖")
    req = Path(__file__).resolve().parent.parent / "requirements.txt"
    if not req.exists():
        req = Path("requirements.txt")
    if req.exists():
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req), "--quiet"],
            timeout=300,
        )
        print("  [OK] 核心依赖安装完成")
    else:
        print("  [WARN] requirements.txt 未找到，跳过")
    # Extra
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "python-dotenv", "--quiet"], timeout=60)


def install_ffmpeg():
    print_step(3, 7, "安装 FFmpeg")
    check = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
    if check.returncode == 0:
        print("  [OK] FFmpeg 已安装")
        return

    print("  [INSTALL] 正在下载 FFmpeg...")
    try:
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        tmp = Path(tempfile.gettempdir()) / "ffmpeg.zip"
        extract_dir = Path(tempfile.gettempdir()) / "ffmpeg_extract"
        urllib.request.urlretrieve(url, tmp)

        import zipfile
        with zipfile.ZipFile(tmp, "r") as zf:
            zf.extractall(extract_dir)

        # Find ffmpeg.exe
        for root, dirs, files in os.walk(extract_dir):
            if "ffmpeg.exe" in files:
                ffmpeg_dir = Path(root)
                target = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "ffmpeg"
                target.mkdir(parents=True, exist_ok=True)
                for f in ffmpeg_dir.glob("*.exe"):
                    shutil.copy(f, target / f.name)
                # Add to PATH
                subprocess.run(
                    ["setx", "PATH", f"{os.environ['PATH']};{target}"],
                    timeout=10,
                )
                print(f"  [OK] FFmpeg 安装到: {target}")
                break

        tmp.unlink()
        shutil.rmtree(extract_dir, ignore_errors=True)
    except Exception as e:
        print(f"  [WARN] FFmpeg 自动安装失败: {e}")
        print("  请手动安装: https://ffmpeg.org/download.html")


def create_env_file():
    print_step(4, 7, "创建配置文件")
    env_template = Path(__file__).resolve().parent.parent / ".env.example"
    env_target = Path(__file__).resolve().parent.parent / ".env"

    if not env_target.exists() and env_template.exists():
        shutil.copy(env_template, env_target)
        print("  [OK] .env 已创建 (从 .env.example 复制)")
        print("  [TODO] 请编辑 .env 填入你的API密钥")
    elif env_target.exists():
        print("  [OK] .env 已存在")
    else:
        # Create minimal .env
        env_target.write_text(
            "# TikTok AI Factory Pro\n"
            "OPENAI_API_KEY=sk-your-key-here\n"
            "ELEVENLABS_API_KEY=your-key-here\n"
            "ARK_API_KEY=ark-your-key-here\n"
        )
        print("  [OK] .env 已创建 (请填入API密钥)")


def create_directories():
    print_step(5, 7, "创建目录结构")
    base = Path(__file__).resolve().parent.parent
    for d in ["input/products", "input/reference_videos", "input/characters", "output", "logs"]:
        (base / d).mkdir(parents=True, exist_ok=True)
        (base / d / ".gitkeep").touch(exist_ok=True)
    print("  [OK] input/ output/ logs/ 已创建")


def create_shortcut():
    print_step(6, 7, "创建桌面快捷方式")
    try:
        import pythoncom
        from win32com.client import Dispatch

        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        shortcut_path = desktop / "TikTok AI Factory.lnk"

        base = Path(__file__).resolve().parent.parent
        target = base / "start" / "启动工厂.bat"
        icon = base / "installer" / "factory.ico"

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(str(shortcut_path))
        shortcut.TargetPath = str(target)
        shortcut.WorkingDirectory = str(base)
        shortcut.Description = "TikTok AI Factory Pro - AI Video Factory"
        shortcut.IconLocation = str(icon) if icon.exists() else ""
        shortcut.Save()

        print(f"  [OK] 桌面快捷方式: {shortcut_path}")
    except ImportError:
        # Simple shortcut via .bat copy
        desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
        shortcut_path = desktop / "TikTok AI Factory.bat"
        base = Path(__file__).resolve().parent.parent
        shortcut_path.write_text(
            f'@echo off\ncd /d "{base}"\nstart "" "{base}\\start\\启动工厂.bat"\n'
        )
        print(f"  [OK] 桌面快捷方式 (bat): {shortcut_path}")
    except Exception as e:
        print(f"  [WARN] 快捷方式创建失败: {e}")


def install_complete():
    print_step(7, 7, "安装完成")
    base = Path(__file__).resolve().parent.parent
    print(f"""
╔══════════════════════════════════════════════╗
║                                              ║
║   TikTok AI Factory Pro — 安装完成!           ║
║                                              ║
║   项目目录: {str(base)[:45]}
║   桌面快捷方式: TikTok AI Factory              ║
║                                              ║
║   [下一步]                                     ║
║   1. 编辑 .env 填入 API 密钥                    ║
║   2. 放入素材到 input/ 目录                      ║
║   3. 双击桌面快捷方式启动                          ║
║                                              ║
╚══════════════════════════════════════════════╝
""")
    input("按 Enter 退出...")


def main():
    run_as_admin()
    os.chdir(Path(__file__).resolve().parent.parent)

    print("\n" + "=" * 60)
    print("  TikTok AI Factory Pro — Windows 安装程序")
    print("=" * 60)

    check_python()
    install_requirements()
    install_ffmpeg()
    create_env_file()
    create_directories()
    create_shortcut()
    install_complete()


if __name__ == "__main__":
    main()
