# VIDEO VALIDATION — output/output001/video.mp4

**验证日期**: 2026-06-10
**验证文件**: `output/output001/video.mp4`

---

## 文件基本信息

| 属性 | 值 |
|------|-----|
| 文件路径 | `output/output001/video.mp4` |
| 文件大小 | 159,440 bytes (155.7 KB) |
| 容器格式 | QuickTime / MOV (isom) |
| 编码器 | **Lavf62.12.101** (ffmpeg) |

---

## 视频流

| 属性 | 值 |
|------|-----|
| 编码 | H.264 (Constrained Baseline) |
| Profile | **Constrained Baseline** |
| 分辨率 | 1080 x 1920 |
| 宽高比 | 9:16 (竖屏) |
| 帧率 | 30 fps |
| 时长 | 14.700 秒 |
| 总帧数 | 441 |
| 码率 | **9.9 kbps** |
| 像素格式 | yuv420p |
| 编码器标识 | **Lavc62.28.101 libx264** |
| Preset特征 | ultrafast (refs=1, has_b_frames=0, Constrained Baseline) |

---

## 音频流

| 属性 | 值 |
|------|-----|
| 编码 | AAC-LC |
| 采样率 | 44100 Hz |
| 声道 | 1 (Mono) |
| 码率 | 69.2 kbps |
| 编码器 | Lavc (ffmpeg) |

---

## 画面内容分析

逐帧像素采样 (5个时间点 × 5个位置 = 25个采样):

| 时间 | 中心(540,960) | 左上(10,10) | 右下 | 判定 |
|------|:---:|:---:|:---:|------|
| 0.5s | RGB(25,23,45) | RGB(25,23,45) | RGB(25,23,45) | 纯色 |
| 3.0s | RGB(25,23,45) | RGB(25,23,45) | RGB(25,23,45) | 纯色 |
| 7.0s | RGB(25,23,45) | RGB(25,23,45) | RGB(25,23,45) | 纯色 |
| 10.0s | RGB(25,23,45) | RGB(25,23,45) | RGB(25,23,45) | 纯色 |
| 14.0s | RGB(25,23,45) | RGB(25,23,45) | RGB(25,23,45) | 纯色 |

**结论**: 全视频所有帧的每个像素都是同一颜色 `RGB(25,23,45)` ≈ `#19172d`。无产品、无人物、无场景、无变化。

---

## 音频内容分析

| 属性 | 值 |
|------|-----|
| 采样分析 | 44100 samples (1秒) |
| 非静音采样 | 984/1000 |
| 零交叉率 | 20次/1000采样 |
| **估计频率** | **441 Hz** |
| **实际频率** | **440 Hz (正弦波)** |

**结论**: 纯440Hz正弦波。无口播、无BGM、无音效。这是ffmpeg `sine=frequency=440` 生成的测试音频。

---

## 生成来源判定

### 证据链

| 证据 | 值 | 来源 |
|------|-----|------|
| 画面颜色 | `0x1a1a2e` | `_generate_placeholder_video()`: `color=c=0x1a1a2e` |
| 音频频率 | 440Hz | `_generate_placeholder_video()`: `sine=frequency=440` |
| 编码器 | Lavf + libx264 | ffmpeg本地编码 |
| Preset | ultrafast / Constrained Baseline | `-preset ultrafast` |
| 视频码率 | 9.9 kbps | 纯色画面极致压缩 |
| 分辨率 | 1080x1920 | 配置中的默认TikTok竖屏尺寸 |
| 时长 | 14.7s | 7镜头 × 2.1s/镜头 = 14.7s |

### 匹配代码

```python
# providers/seedance_provider.py L378-396
# providers/jimeng_provider.py (相同逻辑)

def _generate_placeholder_video(self, duration, width, height, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=0x1a1a2e:s={width}x{height}:d={duration}:r=30",  ← 纯深蓝背景
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",                   ← 440Hz正弦波
        "-c:v", "libx264", "-preset", "ultrafast",                                         ← 超快编码
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        str(output_path),
    ]
```

---

## 最终判定

```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ⚠️  占位视频 (PLACEHOLDER)                              ║
║                                                          ║
║   生成来源:  ffmpeg 本地生成 (非API)                       ║
║   画面内容:  纯色背景 (0x1a1a2e)，无实际内容               ║
║   音频内容:  440Hz 正弦波测试音，无口播/BGM                ║
║   是否来自API:  ❌ 否                                      ║
║   是否真实视频:  ❌ 否                                      ║
║                                                          ║
║   原因: Seedance/即梦 API endpoint 不存在于公网DNS         ║
║         api.seedance.ai → NXDOMAIN                        ║
║         api.jimeng.ai → NXDOMAIN                          ║
║         所有API调用均失败 → 触发 _mock_segment_result()     ║
║         → 全部segments无可用视频 → 触发占位视频生成         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
```

---

## 验证方法

```bash
# 1. 检查像素内容 — 全帧纯色
ffmpeg -ss 5 -i video.mp4 -vframes 1 -f rawvideo -pix_fmt rgb24 - | xxd | head

# 2. 检查音频频率 — 440Hz纯音
ffmpeg -ss 2 -t 1 -i video.mp4 -f s16le -acodec pcm_s16le -ar 44100 -ac 1 - | sox - -n stat 2>&1 | grep Frequency

# 3. 检查编码器签名 — ffmpeg本地生成
ffprobe -v error -show_format -show_streams video.mp4 | grep encoder
# → encoder=Lavf62.12.101  (ffmpeg, 非AI平台)

# 4. 检查API endpoint — 域名不存在
nslookup api.seedance.ai  # → NXDOMAIN
nslookup api.jimeng.ai    # → NXDOMAIN
```
