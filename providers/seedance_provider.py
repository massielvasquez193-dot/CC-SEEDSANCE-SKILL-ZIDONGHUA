"""
TikTok AI Video Factory - Seedance Provider
真实API: 火山引擎 ARK (方舟) 平台
Model: doubao-seedance-2-0-260128

Endpoint:  https://ark.cn-beijing.volces.com/api/v3
Docs:      https://www.volcengine.com/docs/82379/1520757

工作流:
  读取 seedance.txt → 解析镜头 → 逐段调用ARK API → 轮询 → 下载 → 合并 → video.mp4
"""

import json
import logging
import re
import shutil
import time
from pathlib import Path
from typing import Optional

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class SeedanceProvider(BaseProvider):
    provider_name = "seedance"
    supports_text = False
    supports_image = False
    supports_vision = False
    supports_video = True

    # === 真实API配置 ===
    API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
    CREATE_TASK = "/contents/generations/tasks"
    QUERY_TASK  = "/contents/generations/tasks/{task_id}"

    # 模型列表 (选择使用)
    MODEL_STANDARD = "doubao-seedance-2-0-260128"
    MODEL_FAST     = "doubao-seedance-2-0-fast-260128"
    MODEL_LEGACY   = "doubao-seedance-1-5-pro"

    # 支持的分辨率 (优先720p — 2k太慢且贵)
    RESOLUTIONS = {480: "480p", 720: "720p", 1080: "1080p"}

    # 轮询配置
    POLL_INTERVAL = 5
    POLL_MAX_RETRIES = 120  # 最多10分钟

    def _default_model(self) -> str:
        return self.MODEL_STANDARD

    def _create_client(self):
        import requests
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        return session

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            resp = self.client.get(
                f"{self.API_BASE}{self.QUERY_TASK.format(task_id='ping')}",
                timeout=5,
            )
            return resp.status_code in (200, 401, 403, 404)
        except Exception:
            return False

    # ================================================================
    # 核心: 从 seedance.txt 生成完整视频
    # ================================================================
    def generate_from_seedance_txt(
        self,
        seedance_txt_path: Path,
        output_dir: Path,
        keyframes_dir: Path = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 24,
        **kwargs,
    ) -> dict:
        """
        读取 seedance.txt → 解析镜头 → 逐段调用 ARK API → 轮询 → 下载合并 → video.mp4
        """
        if not self.api_key:
            raise RuntimeError(
                "SEEDANCE_API_KEY not set. "
                "Get your key at: https://console.volcengine.com/ark/region:ark+cn-beijing/apikey"
            )

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[Seedance ARK] 从 seedance.txt 生成视频: {seedance_txt_path}")

        # Step 1: 解析
        segments = self._parse_seedance_txt(seedance_txt_path)
        if not segments:
            raise ValueError(f"seedance.txt 解析失败: 未找到有效镜头定义 — {seedance_txt_path}")
        logger.info(f"[Seedance ARK] 解析出 {len(segments)} 个镜头")

        # Step 2: 匹配关键帧
        if keyframes_dir and keyframes_dir.exists():
            self._match_keyframes(segments, keyframes_dir)

        # Step 3: 逐段调用 ARK API
        segment_videos = []
        for i, seg in enumerate(segments):
            logger.info(
                f"[Seedance ARK] 镜头 {seg['shot_id']}/{len(segments)} "
                f"({seg['duration']:.1f}s) → {self.model}"
            )

            result = self._call_ark_api(seg, width, height, fps, **kwargs)
            result["shot_id"] = seg["shot_id"]
            segment_videos.append(result)

            # 下载
            seg_output = output_dir / f"segment_{seg['shot_id']:03d}.mp4"
            if result.get("video_url"):
                self._download_video(result["video_url"], seg_output)
                result["local_path"] = str(seg_output)
                logger.info(f"[Seedance ARK] 镜头 {seg['shot_id']} 下载完成: {seg_output}")
            else:
                raise RuntimeError(
                    f"镜头 {seg['shot_id']} 生成失败: "
                    f"API返回无video_url. task_id={result.get('task_id')}"
                )

            time.sleep(kwargs.get("delay_between_segments", 1.0))

        # Step 4: 合并
        completed_paths = [s["local_path"] for s in segment_videos if s.get("local_path")]
        total_duration = sum(seg["duration"] for seg in segments)
        video_path = output_dir / "video.mp4"

        if len(completed_paths) == 1:
            shutil.copy(completed_paths[0], video_path)
        else:
            self._merge_videos(completed_paths, video_path)

        logger.info(f"[Seedance ARK] 视频生成完成: {video_path} ({len(completed_paths)}/{len(segments)} segments)")

        return {
            "video_path": str(video_path),
            "total_duration": total_duration,
            "segments": segment_videos,
            "status": "completed",
            "segments_completed": len(completed_paths),
            "segments_total": len(segments),
            "api": "volcengine_ark",
            "model": self.model,
        }

    # ================================================================
    # ARK API 调用
    # ================================================================
    def _call_ark_api(
        self,
        seg: dict,
        width: int,
        height: int,
        fps: int,
        **kwargs,
    ) -> dict:
        """调用火山引擎 ARK API — 提交任务 + 轮询 + 获取结果"""
        ref_image = seg.get("reference_image")
        has_ref = ref_image and Path(ref_image).exists()

        # 构建 content 数组 (ARK格式)
        content = [{"type": "text", "text": seg["positive_prompt"]}]
        if has_ref:
            content.append({
                "type": "image_url",
                "image_url": {"url": self._prepare_image(ref_image)},
            })

        # 映射分辨率
        resolution = self.RESOLUTIONS.get(
            min(self.RESOLUTIONS.keys(), key=lambda x: abs(x - max(width, height))),
            "1080p",
        )

        payload = {
            "model": self.model,
            "content": content,
            "parameters": {
                "duration": min(max(seg["duration"], 4), 15),
                "resolution": resolution,
                "fps": fps,
                "generate_audio": kwargs.get("generate_audio", True),
            },
        }

        if seg.get("negative_prompt"):
            payload["parameters"]["negative_prompt"] = seg["negative_prompt"]

        # 保存 debug payload
        self._save_debug_payload(payload, seg["shot_id"])

        # 提交任务
        create_url = f"{self.API_BASE}{self.CREATE_TASK}"
        logger.info(f"[Seedance ARK] POST {create_url}")
        logger.info(f"[Seedance ARK] model={self.model} duration={seg['duration']}s resolution={resolution}")
        logger.info(f"[Seedance ARK] prompt({len(payload['content'][0]['text'])} chars): {payload['content'][0]['text'][:120]}...")

        resp = self.client.post(create_url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            raise RuntimeError(
                f"ARK API 返回异常: 无 task_id. "
                f"HTTP {resp.status_code}, body={json.dumps(data, ensure_ascii=False)[:500]}"
            )

        logger.info(f"[Seedance ARK] 任务已提交: {task_id}")

        # 轮询
        query_url = f"{self.API_BASE}{self.QUERY_TASK.format(task_id=task_id)}"
        poll_interval = kwargs.get("poll_interval", self.POLL_INTERVAL)
        poll_max = kwargs.get("poll_max_retries", self.POLL_MAX_RETRIES)

        for attempt in range(poll_max):
            time.sleep(poll_interval)
            qresp = self.client.get(query_url, timeout=15)
            qresp.raise_for_status()
            qdata = qresp.json()

            status = qdata.get("status", "unknown")

            if status == "succeeded":
                video_url = qdata.get("video_url") or qdata.get("content", {}).get("video_url") or qdata.get("output", {}).get("video_url", "")
                if not video_url:
                    raise RuntimeError(
                        f"ARK 任务 {task_id} 状态为 succeeded 但无 video_url. "
                        f"response={json.dumps(qdata, ensure_ascii=False)[:500]}"
                    )
                return {
                    "video_url": video_url,
                    "task_id": task_id,
                    "duration": seg["duration"],
                    "width": width,
                    "height": height,
                    "format": "mp4",
                    "status": "completed",
                    "api_attempts": attempt + 1,
                }

            elif status in ("failed", "expired", "cancelled"):
                error_msg = qdata.get("error", {}).get("message", "unknown error")
                raise RuntimeError(
                    f"ARK 任务 {task_id} {status}: {error_msg}"
                )

            elif status in ("queued", "running"):
                if attempt % 12 == 0:
                    logger.info(
                        f"  [Seedance ARK] 任务 {task_id[:16]}... "
                        f"状态={status} ({attempt * poll_interval}s)"
                    )
            else:
                logger.warning(f"  [Seedance ARK] 未知状态: {status}")

        raise TimeoutError(
            f"ARK 任务 {task_id} 超时: "
            f"轮询 {poll_max} 次 × {poll_interval}s = {poll_max * poll_interval}s 未完成"
        )

    # ================================================================
    # seedance.txt 解析器
    # ================================================================
    def _parse_seedance_txt(self, txt_path: Path) -> list[dict]:
        content = txt_path.read_text(encoding="utf-8")
        segments = []

        # 全局时长
        global_dur_match = re.search(r'总时长[：:]\s*(\d+)', content)
        total_dur = float(global_dur_match.group(1)) if global_dur_match else 15.0

        # 检测格式类型
        has_markdown_tables = '| 项目 | 内容 |' in content or '|------|------|' in content
        has_prompt_tags = '[正面Prompt]' in content or '[负面Prompt]' in content

        if has_prompt_tags:
            segments = self._parse_legacy_format(content, total_dur)
        elif has_markdown_tables:
            segments = self._parse_markdown_table_format(content, total_dur)
        else:
            segments = self._parse_legacy_format(content, total_dur)

        if not segments:
            raise ValueError(f"seedance.txt 解析失败: 无法识别格式 — {txt_path}")

        logger.info(f"[Seedance ARK] 解析格式: {'prompt-tags' if has_prompt_tags else 'markdown-table' if has_markdown_tables else 'legacy'}, {len(segments)} shots")
        return segments

    def _parse_markdown_table_format(self, content: str, total_dur: float) -> list[dict]:
        """解析 Markdown 表格格式: ### 镜头 N | 项目 | 内容 |"""
        segments = []
        shot_blocks = re.split(r'###\s*镜头\s*(\d+)', content)

        for i in range(1, len(shot_blocks), 2):
            shot_id = int(shot_blocks[i])
            block = shot_blocks[i + 1] if i + 1 < len(shot_blocks) else ""

            # 从 Markdown 表格提取字段
            fields = {}
            for line in block.split('\n'):
                line = line.strip()
                if line.startswith('|') and '|' in line[1:]:
                    parts = [p.strip() for p in line.split('|')[1:-1]]
                    if len(parts) >= 2 and parts[0] not in ('项目', '------', ''):
                        key = parts[0].replace('**', '').strip()
                        val = parts[1].replace('**', '').strip()
                        if key and val and key not in ('---', ':-'):
                            fields[key] = val

            # 提取时长
            duration_str = fields.get('时长', '')
            dur_match = re.search(r'([\d.]+)', str(duration_str))
            shot_duration = float(dur_match.group(1)) if dur_match else round(total_dur / max(len(shot_blocks)//2, 1), 1)

            # 构建正面 prompt — 从表格字段组合自然语言描述
            framing = fields.get('景别', '')
            camera = fields.get('运镜', '')
            action = fields.get('画面描述', '') or fields.get('人物动作', '')
            subtitle = fields.get('字幕', '')
            voiceover = fields.get('口播', '')
            product_pos = fields.get('产品位置', '')
            sfx = fields.get('音效', '')
            transition = fields.get('转场', '')

            prompt_parts = []
            if framing:
                prompt_parts.append(f"{framing} shot")
            if camera:
                prompt_parts.append(f"camera: {camera}")
            if action:
                prompt_parts.append(action)
            if subtitle:
                prompt_parts.append(f"subtitle: {subtitle}")
            if voiceover:
                prompt_parts.append(f"voiceover: {voiceover}")
            if product_pos:
                prompt_parts.append(f"product position: {product_pos}")

            positive = ", ".join(prompt_parts) if prompt_parts else block.strip()

            # 清理 — 确保不包含 markdown 语法
            positive = re.sub(r'\|.*?\|', '', positive)  # 移除残留表格
            positive = re.sub(r'[#*`>]', '', positive)    # 移除 markdown 标记
            positive = re.sub(r'\s+', ' ', positive).strip()
            positive = positive[:2000]  # 限制长度

            segments.append({
                "shot_id": shot_id,
                "duration": min(max(shot_duration, 4), 15),
                "positive_prompt": positive,
                "negative_prompt": self.DEFAULT_NEGATIVE,
                "camera_movement": camera,
                "reference_image": f"keyframe_{shot_id:03d}.jpg",
            })

        return segments

    DEFAULT_NEGATIVE = (
        "blurry, distorted face, extra limbs, deformed hands, bad anatomy, "
        "watermark, text overlay, low quality, grainy, overexposed, underexposed, "
        "harsh shadows, cluttered background, logo, brand name, unrealistic colors"
    )

    def _parse_legacy_format(self, content: str, total_dur: float) -> list[dict]:
        """解析旧格式: ### 镜头 N [正面Prompt] ... [负面Prompt] ..."""
        segments = []
        shot_blocks = re.split(r'###\s*镜头\s*(\d+)', content)

        for i in range(1, len(shot_blocks), 2):
            shot_id = int(shot_blocks[i])
            block = shot_blocks[i + 1] if i + 1 < len(shot_blocks) else ""

            positive = ""
            negative = ""
            camera = ""

            pos_match = re.search(r'\[正面Prompt\]\s*\n(.*?)(?=\[负面Prompt\]|$)', block, re.DOTALL)
            if pos_match:
                positive = pos_match.group(1).strip()

            neg_match = re.search(r'\[负面Prompt\]\s*\n(.*?)(?=###|\Z)', block, re.DOTALL)
            if neg_match:
                negative = neg_match.group(1).strip()

            cam_match = re.search(r'Camera movement:\s*(.+?)$', positive, re.MULTILINE)
            if cam_match:
                camera = cam_match.group(1).strip()

            # 清理 markdown 残留
            positive = re.sub(r'[#*`>|]', '', positive)
            positive = re.sub(r'\s+', ' ', positive).strip()
            negative = re.sub(r'\s+', ' ', negative).strip()

            all_shots = re.findall(r'###\s*镜头\s*(\d+)', content)
            duration = total_dur / max(len(all_shots), 1)

            segments.append({
                "shot_id": shot_id,
                "duration": round(duration, 1),
                "positive_prompt": positive if positive else f"Shot {shot_id} product showcase, cinematic, 9:16 vertical",
                "negative_prompt": negative or self.DEFAULT_NEGATIVE,
                "camera_movement": camera,
                "reference_image": f"keyframe_{shot_id:03d}.jpg",
            })

        return segments

    def _match_keyframes(self, segments: list[dict], keyframes_dir: Path):
        for seg in segments:
            for pattern in [
                f"keyframe_{seg['shot_id']}.jpg",
                f"keyframe_{seg['shot_id']:03d}.jpg",
                f"frame_{seg['shot_id']:04d}.jpg",
            ]:
                candidate = keyframes_dir / pattern
                if candidate.exists():
                    seg["reference_image"] = str(candidate)
                    break

    # ================================================================
    # 基础接口 (BaseProvider)
    # ================================================================
    def _generate_video_impl(self, prompt, negative_prompt, duration, width, height, fps, reference_image, **kwargs) -> dict:
        content = [{"type": "text", "text": prompt}]
        if reference_image:
            content.append({"type": "image_url", "image_url": {"url": self._prepare_image(reference_image)}})

        resolution = self.RESOLUTIONS.get(
            min(self.RESOLUTIONS.keys(), key=lambda x: abs(x - max(width, height))),
            "1080p",
        )

        payload = {
            "model": self.model,
            "content": content,
            "parameters": {
                "duration": min(max(duration, 4), 15),
                "resolution": resolution,
                "fps": fps,
                "generate_audio": True,
            },
        }
        if negative_prompt:
            payload["parameters"]["negative_prompt"] = negative_prompt

        resp = self.client.post(
            f"{self.API_BASE}{self.CREATE_TASK}",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        task_id = data.get("id") or data.get("task_id")

        return {
            "url": "",
            "task_id": task_id,
            "duration": duration,
            "width": width,
            "height": height,
            "format": "mp4",
            "status": "queued",
        }

    def query_task(self, task_id: str) -> dict:
        resp = self.client.get(
            f"{self.API_BASE}{self.QUERY_TASK.format(task_id=task_id)}",
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "unknown")
        return {
            "task_id": task_id,
            "status": status,
            "result_url": data.get("video_url") or data.get("output", {}).get("video_url", ""),
            "progress": 0,
        }

    def generate_segments(self, segments, width=1080, height=1920, fps=24, **kwargs) -> list[dict]:
        results = []
        for seg in segments:
            result = self.generate_video(
                prompt=seg.get("prompt", ""),
                negative_prompt=seg.get("negative_prompt", ""),
                duration=seg.get("duration", 5.0),
                width=width, height=height, fps=fps,
                reference_image=seg.get("reference_image"),
            )
            result["segment_id"] = seg.get("segment_id", len(results) + 1)
            results.append(result)
            time.sleep(kwargs.get("delay_between_segments", 1.0))
        return results

    # ================================================================
    # 下载 & 合并
    # ================================================================
    def _download_video(self, url: str, output_path: Path):
        import requests
        logger.info(f"[Seedance ARK] 下载视频: {url[:80]}...")
        resp = requests.get(url, stream=True, timeout=600)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
        logger.info(f"[Seedance ARK] 已保存: {output_path} ({output_path.stat().st_size} bytes)")

    def _merge_videos(self, video_paths: list, output_path: Path):
        import subprocess
        concat_list = output_path.parent / "concat_list.txt"
        with open(concat_list, "w") as f:
            for vp in video_paths:
                p = Path(vp) if isinstance(vp, str) else vp
                f.write(f"file '{p.resolve()}'\n")
        result = subprocess.run([
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", str(concat_list), "-c", "copy",
            str(output_path), "-y",
        ], capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"视频合并失败: {result.stderr[:300]}")
        logger.info(f"[Seedance ARK] 视频合并完成: {output_path}")

    def _save_debug_payload(self, payload: dict, shot_id: int):
        """保存发送给ARK的payload到 output/debug_payload.json"""
        try:
            debug_path = Path("output/debug_payload.json")
            existing = {}
            if debug_path.exists():
                try:
                    existing = json.loads(debug_path.read_text(encoding="utf-8"))
                except Exception:
                    existing = {}
            existing[f"shot_{shot_id}"] = {
                "model": payload.get("model"),
                "content_text_preview": str(payload.get("content", [{}])[0].get("text", ""))[:200],
                "content_text_length": len(str(payload.get("content", [{}])[0].get("text", ""))),
                "parameters": payload.get("parameters"),
                "has_image": len(payload.get("content", [])) > 1,
            }
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            debug_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to save debug payload: {e}")

    def _prepare_image(self, image_path: str) -> str:
        if image_path.startswith(("http://", "https://", "data:")):
            return image_path
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"参考图片不存在: {image_path}")
        import base64
        suffix = path.suffix.lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
        mime = mime_map.get(suffix, "image/jpeg")
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{data}"
