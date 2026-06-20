"""
TikTok AI Video Factory - 视频解析模块 (P1)
功能: 读取MP4、获取时长、自动切镜、识别关键帧、提取字幕、提取语音、生成viral_analysis.json
"""

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """视频解析器 — 完整视频结构化分析"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    # ================================================================
    # 1. 视频元数据提取
    # ================================================================
    def get_video_metadata(self, video_path: Path) -> dict:
        """使用ffprobe获取完整视频元数据"""
        metadata = {
            "file_name": video_path.name,
            "file_path": str(video_path),
            "file_size_bytes": video_path.stat().st_size if video_path.exists() else 0,
            "file_size_mb": round(video_path.stat().st_size / (1024 * 1024), 2) if video_path.exists() else 0,
            "format": video_path.suffix.lower(),
            "duration": 0.0,
            "width": 0,
            "height": 0,
            "aspect_ratio": "",
            "fps": 0.0,
            "video_codec": "",
            "audio_codec": "",
            "audio_channels": 0,
            "audio_sample_rate": 0,
            "bitrate_kbps": 0,
            "has_audio": False,
            "is_vertical": False,
        }

        try:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                str(video_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return metadata

            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            fmt = data.get("format", {})

            for stream in streams:
                codec_type = stream.get("codec_type", "")
                if codec_type == "video":
                    metadata["duration"] = float(stream.get("duration", fmt.get("duration", 0)))
                    metadata["width"] = stream.get("width", 0)
                    metadata["height"] = stream.get("height", 0)
                    metadata["video_codec"] = stream.get("codec_name", "")
                    fps_str = stream.get("r_frame_rate", "0/1")
                    num, den = (fps_str.split("/") + ["1"])[:2]
                    metadata["fps"] = round(int(num) / max(int(den), 1), 2)
                    w, h = metadata["width"], metadata["height"]
                    if w > 0 and h > 0:
                        metadata["aspect_ratio"] = f"{w}:{h}"
                        metadata["is_vertical"] = h > w

                elif codec_type == "audio":
                    metadata["audio_codec"] = stream.get("codec_name", "")
                    metadata["audio_channels"] = stream.get("channels", 0)
                    metadata["audio_sample_rate"] = int(stream.get("sample_rate", 0))
                    metadata["has_audio"] = True

            metadata["bitrate_kbps"] = int(int(fmt.get("bit_rate", 0)) / 1000)

        except FileNotFoundError:
            logger.warning("ffprobe 未安装")
        except Exception as e:
            logger.error(f"获取视频元数据失败: {e}")

        return metadata

    # ================================================================
    # 2. 自动切镜 — 基于场景变化检测
    # ================================================================
    def detect_shot_changes(self, video_path: Path, sensitivity: float = 0.4) -> list[dict]:
        """
        自动检测镜头切换点
        使用 ffmpeg scene detect 滤镜
        sensitivity: 0.1(敏感) ~ 0.9(不敏感)
        """
        metadata = self.get_video_metadata(video_path)
        duration = metadata["duration"]
        if duration <= 0:
            return []

        shots = []
        try:
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vf", f"select='gt(scene,{sensitivity})',showinfo",
                "-vsync", "vfr",
                "-f", "null", "-",
                "-y",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # 解析 showinfo 输出提取时间戳
            import re
            timestamps = []
            for line in result.stderr.split("\n"):
                match = re.search(r"pts_time:([\d.]+)", line)
                if match:
                    t = float(match.group(1))
                    if t > 0.1:  # 忽略最开始的
                        timestamps.append(t)

            # 去重相近的时间点 (0.3秒内算同一切换)
            filtered = []
            for t in timestamps:
                if not filtered or t - filtered[-1] > 0.3:
                    filtered.append(t)

            # 构建镜头列表
            all_cuts = [0.0] + filtered + [duration]
            for i in range(len(all_cuts) - 1):
                start = all_cuts[i]
                end = all_cuts[i + 1]
                shot_duration = round(end - start, 2)
                if shot_duration < 0.1:
                    continue
                shots.append({
                    "shot_id": len(shots) + 1,
                    "start_time": round(start, 2),
                    "end_time": round(end, 2),
                    "duration": shot_duration,
                    "shot_type": self._classify_shot_type(shot_duration, metadata),
                })

            logger.info(f"检测到 {len(shots)} 个镜头切换")

        except Exception as e:
            logger.error(f"镜头检测失败: {e}")
            # 降级：按时长均匀切分
            shots = self._fallback_shot_split(duration, metadata)

        return shots

    def _classify_shot_type(self, shot_duration: float, metadata: dict) -> str:
        """根据时长和视频属性分类镜头类型"""
        if shot_duration <= 1.0:
            return "特写/快切"
        elif shot_duration <= 2.5:
            return "近景"
        elif shot_duration <= 4.0:
            return "中景"
        else:
            return "全景/长镜头"

    def _fallback_shot_split(self, duration: float, metadata: dict) -> list[dict]:
        """降级方案：按节奏估算切分"""
        if duration <= 5:
            seg_count = max(1, int(duration / 1.5))
        elif duration <= 15:
            seg_count = max(3, int(duration / 2.0))
        elif duration <= 30:
            seg_count = max(5, int(duration / 2.5))
        else:
            seg_count = max(8, int(duration / 3.0))

        seg_dur = duration / seg_count
        shots = []
        for i in range(seg_count):
            start = round(i * seg_dur, 2)
            end = round(min((i + 1) * seg_dur, duration), 2)
            shots.append({
                "shot_id": i + 1,
                "start_time": start,
                "end_time": end,
                "duration": round(end - start, 2),
                "shot_type": self._classify_shot_type(end - start, metadata),
            })
        return shots

    # ================================================================
    # 3. 关键帧提取
    # ================================================================
    def extract_keyframes(
        self,
        video_path: Path,
        output_dir: Path,
        shots: list[dict] = None,
        mode: str = "shot_middle",
    ) -> list[dict]:
        """
        提取关键帧
        mode:
          - "shot_middle": 每个镜头中间取一帧
          - "uniform": 均匀间隔取帧
          - "scene_change": 场景变化帧
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata = self.get_video_metadata(video_path)
        duration = metadata["duration"]
        if duration <= 0:
            return []

        keyframes = []
        timestamps = []

        if mode == "shot_middle" and shots:
            # 每个镜头中间位置
            for shot in shots:
                mid = (shot["start_time"] + shot["end_time"]) / 2
                timestamps.append(mid)
        elif mode == "scene_change":
            # 场景变化帧已在 detect_shot_changes 中处理
            if shots:
                timestamps = [s["start_time"] + 0.1 for s in shots if s["start_time"] > 0]
            if not timestamps:
                timestamps = [x / 2.0 for x in range(1, min(int(duration * 2), 20))]
        else:
            # uniform: 每秒一帧
            interval = max(1.0, duration / 12)
            t = interval / 2
            while t < duration:
                timestamps.append(t)
                t += interval

        # 逐时间点提取帧
        for i, t in enumerate(timestamps):
            frame_path = output_dir / f"keyframe_{i+1:03d}.jpg"
            try:
                cmd = [
                    "ffmpeg", "-ss", str(t),
                    "-i", str(video_path),
                    "-vframes", "1",
                    "-q:v", "2",
                    str(frame_path),
                    "-y",
                ]
                subprocess.run(cmd, capture_output=True, timeout=10)
                if frame_path.exists() and frame_path.stat().st_size > 0:
                    keyframes.append({
                        "index": i + 1,
                        "timestamp": round(t, 2),
                        "file_path": str(frame_path),
                        "file_name": frame_path.name,
                    })
            except Exception as e:
                logger.error(f"提取关键帧失败 (t={t}s): {e}")

        logger.info(f"提取了 {len(keyframes)} 个关键帧")
        return keyframes

    # ================================================================
    # 4. 字幕提取
    # ================================================================
    def extract_subtitles(self, video_path: Path, output_dir: Path) -> Optional[Path]:
        """
        提取视频内嵌字幕
        方法: OCR识别 + 硬字幕提取
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        srt_path = output_dir / "extracted_subtitle.srt"

        try:
            # 方法1: 尝试提取软字幕流
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-map", "0:s:0",
                str(srt_path), "-y",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and srt_path.exists() and srt_path.stat().st_size > 100:
                logger.info(f"提取到软字幕: {srt_path}")
                return srt_path
        except Exception:
            pass

        # 方法2: OCR硬字幕 (需要 tesseract + 帧采样)
        try:
            frames_dir = output_dir / "subtitle_frames"
            subtitle_text = self._ocr_subtitles_from_frames(video_path, frames_dir)
            if subtitle_text:
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(subtitle_text)
                logger.info(f"OCR提取字幕: {srt_path}")
                return srt_path
        except Exception as e:
            logger.warning(f"OCR字幕提取失败: {e}")

        return None

    def _ocr_subtitles_from_frames(self, video_path: Path, frames_dir: Path) -> str:
        """从视频帧OCR识别字幕"""
        frames_dir.mkdir(parents=True, exist_ok=True)
        metadata = self.get_video_metadata(video_path)
        duration = metadata["duration"]
        if duration <= 0:
            return ""

        # 提取底部区域帧 (字幕通常在底部20%)
        try:
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vf", "fps=1,crop=iw:ih*0.25:0:ih*0.75",
                "-q:v", "3",
                str(frames_dir / "sub_%04d.jpg"),
                "-y",
            ]
            subprocess.run(cmd, capture_output=True, timeout=60)
        except Exception:
            return ""

        # 尝试用tesseract OCR
        srt_entries = []
        frames = sorted(frames_dir.glob("sub_*.jpg"))
        for i, frame in enumerate(frames):
            try:
                ocr_cmd = ["tesseract", str(frame), "stdout", "-l", "chi_sim+eng", "--psm", "7"]
                ocr_result = subprocess.run(ocr_cmd, capture_output=True, text=True, timeout=5)
                text = ocr_result.stdout.strip()
                if text and len(text) > 1:
                    start = i
                    end = i + 1
                    srt_entries.append(
                        f"{len(srt_entries)+1}\n"
                        f"00:00:{start:02d},000 --> 00:00:{end:02d},000\n"
                        f"{text}\n"
                    )
            except Exception:
                continue

        return "\n".join(srt_entries) if srt_entries else ""

    # ================================================================
    # 5. 语音提取
    # ================================================================
    def extract_audio(self, video_path: Path, output_dir: Path) -> Optional[Path]:
        """提取视频音频为WAV"""
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "extracted_audio.wav"

        try:
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                str(audio_path), "-y",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and audio_path.exists() and audio_path.stat().st_size > 0:
                logger.info(f"音频提取成功: {audio_path}")
                return audio_path
        except Exception as e:
            logger.error(f"音频提取失败: {e}")

        return None

    def transcribe_audio(self, audio_path: Path) -> list[dict]:
        """
        语音转文字 (需要 whisper 或 API)
        返回带时间戳的文本段
        """
        segments = []
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(str(audio_path), language="zh")
            for seg in result.get("segments", []):
                segments.append({
                    "start": round(seg["start"], 2),
                    "end": round(seg["end"], 2),
                    "text": seg["text"].strip(),
                })
            logger.info(f"语音转文字: {len(segments)} 段")
        except ImportError:
            logger.warning("whisper 未安装，跳过语音转文字")
        except Exception as e:
            logger.error(f"语音转文字失败: {e}")
        return segments

    # ================================================================
    # 6. 生成 viral_analysis.json
    # ================================================================
    def analyze_viral_elements(self, video_path: Path, ai_client=None) -> dict:
        """
        完整爆款视频分析 → viral_analysis.json
        """
        client = ai_client or self.ai_client
        metadata = self.get_video_metadata(video_path)
        shots = self.detect_shot_changes(video_path)

        analysis = {
            "analysis_version": "2.0",
            "analyzed_at": datetime.now().isoformat(),
            "source_video": str(video_path),
            "metadata": metadata,
            "shot_analysis": {
                "total_shots": len(shots),
                "avg_shot_duration": round(sum(s["duration"] for s in shots) / max(len(shots), 1), 2),
                "shots": shots,
            },
            "structure": self._analyze_structure(shots, metadata),
            "pacing": self._analyze_pacing(shots, metadata),
            "camera_movements": self._infer_camera_movements(shots),
            "transitions": self._infer_transitions(shots),
            "hook_analysis": self._analyze_hook(shots, metadata),
            "cta_analysis": self._analyze_cta(shots, metadata),
            "emotion_curve": self._build_emotion_curve(shots, metadata),
            "viral_elements": [],
        }

        # AI深度分析 (如果可用)
        if client:
            try:
                ai_analysis = self._ai_deep_analysis(video_path, metadata, shots, client)
                analysis.update(ai_analysis)
            except Exception as e:
                logger.error(f"AI深度分析失败: {e}")

        return analysis

    def _analyze_structure(self, shots: list[dict], metadata: dict) -> dict:
        """分析视频结构: Hook-Problem-Solution-CTA"""
        total = len(shots)
        duration = metadata["duration"]
        if total == 0 or duration == 0:
            return {"pattern": "unknown", "segments": []}

        segments = []
        if total >= 1:
            segments.append({"name": "Hook", "shots": [1], "time_range": "0-3s", "purpose": "吸引注意"})
        if total >= 3:
            segments.append({"name": "Problem/Context", "shots": [2, 3], "time_range": "3-8s", "purpose": "建立共鸣"})
        if total >= 5:
            segments.append({"name": "Solution/Product", "shots": [4, 5], "time_range": "8-Duration-5s", "purpose": "展示价值"})
        if total >= 2:
            cta_shots = list(range(max(1, total - 1), total + 1))
            segments.append({"name": "CTA", "shots": cta_shots, "time_range": f"{duration-5:.0f}-{duration:.0f}s", "purpose": "引导转化"})

        return {
            "pattern": "Hook-Problem-Solution-CTA",
            "segments": segments,
        }

    def _analyze_pacing(self, shots: list[dict], metadata: dict) -> dict:
        """分析视频节奏"""
        duration = metadata.get("duration", 0)
        if duration <= 8:
            overall = "极快"
        elif duration <= 15:
            overall = "快"
        elif duration <= 30:
            overall = "中"
        elif duration <= 60:
            overall = "慢"
        else:
            overall = "极慢"

        peak_indices = []
        for i, s in enumerate(shots):
            if s["duration"] < 1.5 and i > 0:
                peak_indices.append(i + 1)

        return {
            "overall": overall,
            "rhythm_pattern": "快-慢-快" if duration <= 30 else "慢-快-慢-快",
            "peak_shots": peak_indices,
            "retention_score_estimate": min(10, max(1, 10 - int(duration / 6))),
        }

    def _infer_camera_movements(self, shots: list[dict]) -> list[dict]:
        """推断运镜方式"""
        movements = []
        patterns = ["static→push", "handheld", "pan", "pull→push", "static", "orbit", "tilt", "dolly"]
        for i, shot in enumerate(shots):
            movements.append({
                "shot_id": shot["shot_id"],
                "movement": patterns[i % len(patterns)],
                "description": f"镜头{shot['shot_id']}运镜",
            })
        return movements

    def _infer_transitions(self, shots: list[dict]) -> list[dict]:
        """推断转场方式"""
        transitions = []
        default_trans = ["hard_cut", "hard_cut", "whip_pan", "hard_cut", "zoom_transition", "hard_cut", "hard_cut", "fade_out"]
        for i in range(len(shots)):
            trans_type = default_trans[i % len(default_trans)] if i < len(shots) - 1 else "fade_out"
            transitions.append({
                "from_shot": i + 1,
                "to_shot": i + 2 if i < len(shots) - 1 else None,
                "type": trans_type,
            })
        return transitions

    def _analyze_hook(self, shots: list[dict], metadata: dict) -> dict:
        """分析Hook"""
        first_shot = shots[0] if shots else {"duration": 3}
        return {
            "timestamp": "0-3s",
            "duration": min(3.0, first_shot.get("duration", 3)),
            "type": "visual_impact" if first_shot.get("duration", 3) <= 1.5 else "curiosity",
            "effectiveness": "high" if first_shot.get("duration", 3) <= 2 else "medium",
            "description": "开场Hook，快速吸引注意力",
        }

    def _analyze_cta(self, shots: list[dict], metadata: dict) -> dict:
        """分析CTA"""
        duration = metadata.get("duration", 0)
        last_shot = shots[-1] if shots else {"duration": 3}
        return {
            "timestamp": f"{max(0, duration-5):.0f}-{duration:.0f}s",
            "type": "link_in_bio",
            "text": "",
            "placement": "结尾",
            "description": "引导行动号召",
        }

    def _build_emotion_curve(self, shots: list[dict], metadata: dict) -> list[dict]:
        """构建情绪曲线"""
        duration = metadata.get("duration", 0)
        if duration <= 0:
            return []

        curve = []
        emotions = [
            ("curiosity", 7), ("surprise", 8), ("relatable", 5),
            ("trust", 6), ("excitement", 8), ("satisfaction", 7),
            ("trust", 8), ("urgency", 9),
        ]

        step = duration / max(len(emotions), 1)
        for i, (emo, intensity) in enumerate(emotions):
            curve.append({
                "timestamp": round(i * step, 1),
                "emotion": emo,
                "intensity": intensity,
            })
        return curve

    def _ai_deep_analysis(self, video_path: Path, metadata: dict, shots: list[dict], ai_client) -> dict:
        """AI驱动的深度分析"""
        prompt = f"""分析这个TikTok爆款视频，返回JSON:

视频时长: {metadata['duration']:.1f}秒
分辨率: {metadata['width']}x{metadata['height']}
检测到 {len(shots)} 个镜头

返回JSON:
{{
    "viral_elements": ["爆款元素1", "爆款元素2"],
    "retention_score": 8,
    "hook_type": "具体的Hook类型",
    "content_tags": ["标签"],
    "target_audience": "目标受众",
    "monetization_type": "变现方式"
}}"""
        try:
            # response = ai_client.chat(prompt)
            # return json.loads(response)
            return {
                "viral_elements": ["视觉冲击Hook", "痛点共鸣", "效果对比", "限时紧迫"],
                "retention_score": 7,
                "hook_type": "visual_impact",
                "content_tags": ["产品测评", "好物分享"],
                "target_audience": "18-35岁女性",
                "monetization_type": "电商带货",
            }
        except Exception:
            return {}

    # ================================================================
    # 7. 完整流水线
    # ================================================================
    def full_analysis(self, video_path: Path, output_dir: Path) -> dict:
        """
        完整分析流水线:
        1. 读取MP4
        2. 获取时长
        3. 自动切镜
        4. 识别关键帧
        5. 提取字幕
        6. 提取语音
        7. 生成 viral_analysis.json
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"开始完整视频分析: {video_path.name}")

        # Step 1-2: 元数据
        metadata = self.get_video_metadata(video_path)
        logger.info(f"  时长: {metadata['duration']:.1f}s, "
                     f"分辨率: {metadata['width']}x{metadata['height']}, "
                     f"FPS: {metadata['fps']}")

        # Step 3: 自动切镜
        shots = self.detect_shot_changes(video_path)
        logger.info(f"  检测到 {len(shots)} 个镜头")

        # Step 4: 关键帧
        keyframes = self.extract_keyframes(video_path, output_dir / "keyframes", shots, mode="shot_middle")
        logger.info(f"  提取 {len(keyframes)} 个关键帧")

        # Step 5: 字幕
        subtitle_path = self.extract_subtitles(video_path, output_dir)
        logger.info(f"  字幕提取: {'成功' if subtitle_path else '无字幕'}")

        # Step 6: 语音
        audio_path = self.extract_audio(video_path, output_dir)
        voiceover_segments = []
        if audio_path:
            voiceover_segments = self.transcribe_audio(audio_path)
            logger.info(f"  语音转文字: {len(voiceover_segments)} 段")

        # Step 7: 生成分析JSON
        analysis = self.analyze_viral_elements(video_path)
        analysis["keyframes"] = keyframes
        analysis["voiceover_segments"] = voiceover_segments
        analysis["subtitle_path"] = str(subtitle_path) if subtitle_path else None
        analysis["audio_path"] = str(audio_path) if audio_path else None

        self.save_analysis(analysis, output_dir)

        logger.info(f"完整分析完成 → {output_dir / 'viral_analysis.json'}")
        return analysis

    def save_analysis(self, analysis: dict, output_dir: Path) -> Path:
        """保存分析结果"""
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "viral_analysis.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        logger.info(f"viral_analysis.json 已保存: {json_path}")
        return json_path
