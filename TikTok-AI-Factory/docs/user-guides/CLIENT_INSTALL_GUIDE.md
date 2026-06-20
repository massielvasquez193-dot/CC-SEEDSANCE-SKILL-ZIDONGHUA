# 客户端安装指南 — TikTok AI Factory Pro

---

## 一、系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Windows 10 (64位) | Windows 11 (64位) |
| 内存 | 8 GB | 16 GB |
| 硬盘 | 5 GB 可用空间 | 20 GB SSD |
| 网络 | 需访问外网 (API调用) | 稳定宽带 |
| Python | 3.10+ | 3.11 |

---

## 二、安装步骤

### 方式1: 一键安装 (推荐)

```
1. 双击: TikTok-AI-Factory-Pro-Setup-v3.0.0.exe
2. 选择安装目录 (默认: C:\Program Files\TikTok-AI-Factory-Pro)
3. 勾选"创建桌面快捷方式"
4. 点击"安装"
5. 等待自动完成 (约3-5分钟)
```

安装程序会自动:
- ✅ 检测/安装 Python 3.11
- ✅ 安装所有依赖包
- ✅ 安装 FFmpeg
- ✅ 创建目录结构
- ✅ 生成桌面快捷方式

### 方式2: 手动安装

```bash
# 1. 安装 Python 3.11+
#    下载: https://www.python.org/downloads/
#    ⚠️ 安装时勾选 "Add Python to PATH"

# 2. 解压项目包到任意目录

# 3. 双击安装依赖
双击: install/01_安装依赖.bat

# 4. 检测环境
双击: install/02_检测环境.bat
```

---

## 三、API密钥配置

安装完成后，需要配置API密钥才能使用AI功能。

### 3.1 获取密钥

| 服务 | 用途 | 获取地址 | 费用 |
|------|------|---------|------|
| OpenAI | GPT脚本 + GPT Image关键帧 | https://platform.openai.com/api-keys | 按量付费 |
| ElevenLabs | 真人配音 | https://elevenlabs.io/app/settings/api-keys | 免费10K字符/月 |
| 火山引擎ARK | Seedance视频生成 | https://console.volcengine.com/ark/ | 新用户送500万tokens |

### 3.2 配置方法

```
1. 打开项目目录下的 .env 文件 (用记事本)
2. 填入你的API密钥:

OPENAI_API_KEY=sk-你的OpenAI密钥
ELEVENLABS_API_KEY=你的ElevenLabs密钥
ARK_API_KEY=ark-你的火山引擎密钥

3. 保存文件
```

⚠️ **最少配置**: 至少需要 `OPENAI_API_KEY`。没有视频生成密钥时，系统会生成脚本/口播/字幕/分镜，只是跳过视频生成步骤。

---

## 四、验证安装

```bash
# 双击桌面快捷方式 "TikTok AI Factory"
# 或命令行:
python run_factory.py --status
```

正常输出:
```
产品图片: 可检测
参考视频: 可检测
人物图片: 可检测
Provider: openai | model=gpt-4.1
就绪状态: 可以启动
```

---

## 五、常见安装问题

| 问题 | 解决 |
|------|------|
| "python不是内部命令" | Python未安装或未添加到PATH。重新安装Python并勾选"Add Python to PATH" |
| "ffmpeg未找到" | 安装FFmpeg: https://ffmpeg.org/download.html |
| "pip安装失败" | 网络问题。尝试: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple |
| "API Key无效" | 检查.env文件中的密钥是否正确，注意不要有多余空格 |
| "401/403错误" | API密钥余额不足或未开通对应服务 |

---

*安装完成后，请阅读 CLIENT_USER_GUIDE.md 了解如何使用。*
