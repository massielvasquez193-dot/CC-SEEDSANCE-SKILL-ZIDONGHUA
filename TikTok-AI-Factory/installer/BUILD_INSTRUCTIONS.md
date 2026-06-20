# TikTok AI Factory Pro v1.0 — Build Instructions

## 构建流程

### Step 1: 准备发布文件
```bash
cd ../
python tools/release_builder.py
# Output: release/client/ (clean client package)
```

### Step 2: 构建 launcher.exe (PyInstaller)
```bash
pip install pyinstaller
pyinstaller installer/launcher.spec
# Output: dist/launcher.exe
```

### Step 3: 构建 Setup.exe (Inno Setup)
1. 安装 Inno Setup: https://jrsoftware.org/isinfo.php
2. 打开 `installer/setup_v1.iss`
3. 点击 Compile (或命令行: `iscc installer/setup_v1.iss`)
4. Output: `installer/output/TikTok-AI-Factory-Pro-v1.0-Setup.exe`

### Step 4: 测试安装
1. 运行 `TikTok-AI-Factory-Pro-v1.0-Setup.exe`
2. 验证安装目录结构
3. 验证桌面快捷方式
4. 验证启动 + API 向导
5. 测试卸载

## 一键构建
```bash
python tools/release_builder.py && ^
pyinstaller installer/launcher.spec && ^
iscc installer/setup_v1.iss
```

## 输出文件
- `dist/launcher.exe` — PyInstaller 打包的可执行文件
- `installer/output/TikTok-AI-Factory-Pro-v1.0-Setup.exe` — 最终安装包
