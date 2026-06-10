"""
TikTok AI Video Factory - 即梦 (Jimeng) Provider
真实API: 火山引擎 ARK (方舟) 平台 — 即梦AI视频生成
Docs: https://www.volcengine.com/docs/85621/1792710

即梦 = 字节跳动 AI创作平台，底层模型为 Seedance/Seedream 系列
通过火山引擎 ARK 统一 API 对外提供服务

Endpoint: https://ark.cn-beijing.volces.com/api/v3
工作流:
  读取 jimeng.txt → 解析镜头 → 逐段调用ARK API → 轮询 → 下载 → 合并 → video.mp4
"""

import logging
import re
import shutil
import time
from pathlib import Path
from typing import Optional

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class JimengProvider(BaseProvider):
    provider_name = "jimeng"
    supports_text = False
    supports_image = True
    supports_vision = False
    supports_video = True

    # === 真实API配置 (火山引擎 ARK) ===
    API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
    CREATE_TASK = "/contents/generations/tasks"
    QUERY_TASK  = "/contents/generations/tasks/{task_id}"

    # 即梦可用模型
    MODEL_JIMENG_3_720P  = "jimeng-video-3-0-720p"
    MODEL_JIMENG_3_1080P = "jimeng-video-3-0-1080p"
    MODEL_JIMENG_3_PRO   = "jimeng-video-3-0-pro"
    MODEL_SEEDANCE_2     = "doubao-seedance-2-0-260128"
    MODEL_SEEDANCE_2_FAST = "doubao-seedance-2-0-fast-260128"

    RESOLUTIONS = {480: "480p", 720: "720p", 1080: "1080p", 2048: "2k"}

    POLL_INTERVAL = 5
    POLL_MAX_RETRIES = 120

    def _default_model(self) -> str:
        return self.MODEL_JIMENG_3_1080P

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
    # 核心: 从 jimeng.txt 生成完整视频
    # ================================================================
    def generate_from_jimeng_txt(
        self,
        jimeng_txt_path: Path,
        output_dir: Path,
        keyframes_dir: Path = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 24,
        **kwargs,
    ) -> dict:
        """
        读取 jimeng.txt → 解析镜头 → 逐段调用ARK API → 下载合并 → video.mp4
        """
        if not self.api_key:
            raise RuntimeError(
                "JIMENG_API_KEY not set. "
                "Get your key at: https://console.volcengine.com/ark/region:ark+cn-beijing/apikey"
            )

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[Jimeng ARK] 从 jimeng.txt 生成视频: {jimeng_txt_path}")

        # Step 1: 解析
        segments = self._parse_jimeng_txt(jimeng_txt_path)
        if not segments:
            raise ValueError(f"jimeng.txt 解析失败: 未找到有效镜头定义 — {jimeng_txt_path}")
        logger.info(f"[Jimeng ARK] 解析出 {len(segments)} 个镜头")

        # Step 2: 匹配参考图
        if keyframes_dir and keyframes_dir.exists():
            self._match_reference_images(segments, keyframes_dir)

        # Step 3: 逐段生成
        segment_videos = []
        for i, seg in enumerate(segments):
            logger.info(
                f"[Jimeng ARK] 镜头 {seg['shot_id']}/{len(segments)} "
                f"({seg['duration']:.1f}s) → {self.model}"
            )

            result = self._call_ark_api(seg, width, height, fps, **kwargs)
            result["shot_id"] = seg["shot_id"]
            segment_videos.append(result)

            seg_output = output_dir / f"segment_{seg['shot_id']:03d}.mp4"
            if result.get("video_url"):
                self._download_video(result["video_url"], seg_output)
                result["local_path"] = str(seg_output)
                logger.info(f"[Jimeng ARK] 镜头 {seg['shot_id']} 下载完成: {seg_output}")
            else:
                raise RuntimeError(
                    f"镜头 {seg['shot_id']} 生成失败: "
                    f"API返回无 video_url. task_id={result.get('task_id')}"
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

        logger.info(f"[Jimeng ARK] 视频生成完成: {video_path} ({len(completed_paths)}/{len(segments)} segments)")

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
    def _call_ark_api(self, seg: dict, width: int, height: int, fps: int, **kwargs) -> dict:
        """调用火山引擎 ARK API — 即梦视频生成"""
        ref_image = seg.get("reference_image")
        has_ref = ref_image and Path(ref_image).exists()

        content = [{"type": "text", "text": seg["positive_prompt"]}]
        if has_ref:
            content.append({
                "type": "image_url",
                "image_url": {"url": self._prepare_image(ref_image)},
            })

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

        create_url = f"{self.API_BASE}{self.CREATE_TASK}"
        logger.debug(f"[Jimeng ARK] POST {create_url} | model={self.model}")

        resp = self.client.post(create_url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            raise RuntimeError(
                f"ARK API 返回异常: 无 task_id. "
                f"HTTP {resp.status_code}, body={json.dumps(data, ensure_ascii=False)[:500]}"
            )

        logger.info(f"[Jimeng ARK] 任务已提交: {task_id}")

        # 轮询
        import json
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
                video_url = qdata.get("video_url") or qdata.get("output", {}).get("video_url", "")
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
                raise RuntimeError(f"ARK 任务 {task_id} {status}: {error_msg}")

            elif status in ("queued", "running"):
                if attempt % 12 == 0:
                    logger.info(f"  [Jimeng ARK] 任务 {task_id[:16]}... 状态={status} ({attempt * poll_interval}s)")

        raise TimeoutError(
            f"ARK 任务 {task_id} 超时: {poll_max * poll_interval}s 未完成"
        )

    # ================================================================
    # jimeng.txt 解析器
    # ================================================================
    def _parse_jimeng_txt(self, txt_path: Path) -> list[dict]:
        content = txt_path.read_text(encoding="utf-8")
        segments = []

        total_duration = 15.0
        dur_match = re.search(r'时长[：:]\s*约?\s*(\d+)', content)
        if dur_match:
            total_duration = float(dur_match.group(1))

        character_consistency = ""
        char_match = re.search(
            r'人物一致性要求.*?\n(.*?)(?=## 镜头拆解|## 产品一致性|\Z)',
            content, re.DOTALL,
        )
        if char_match:
            character_consistency = char_match.group(1).strip()

        shot_blocks = re.split(r'###\s*镜头\s*(\d+)', content)

        for i in range(1, len(shot_blocks), 2):
            shot_id = int(shot_blocks[i])
            block = shot_blocks[i + 1] if i + 1 < len(shot_blocks) else ""

            positive = ""
            negative = ""

            neg_match = re.search(r'负面提示词[：:]\s*\n?(.*?)(?=###|\Z)', block, re.DOTALL)
            if neg_match:
                negative = neg_match.group(1).strip()
                positive = block[:neg_match.start()].strip()
            else:
                positive = block.strip()

            segments.append({
                "shot_id": shot_id,
                "duration": round(total_duration / max(len(shot_blocks) // 2, 1), 1),
                "positive_prompt": positive.strip(),
                "negative_prompt": negative,
                "character_consistency": character_consistency,
                "reference_image": f"keyframe_{shot_id:03d}.jpg",
            })

        return segments

    def _match_reference_images(self, segments: list[dict], keyframes_dir: Path):
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
            "url": "", "task_id": task_id,
            "duration": duration, "width": width, "height": height,
            "format": "mp4", "status": "queued",
        }

    def _generate_image_impl(self, prompt, negative_prompt, width, height, num_images, **kwargs) -> list[dict]:
        content = [{"type": "text", "text": prompt}]
        resolution = self.RESOLUTIONS.get(
            min(self.RESOLUTIONS.keys(), key=lambda x: abs(x - max(width, height))),
            "1080p",
        )
        payload = {
            "model": "doubao-seedream-4-0",
            "content": content,
            "parameters": {"resolution": resolution, "n": num_images},
        }
        resp = self.client.post(
            f"{self.API_BASE}{self.CREATE_TASK}",
            json=payload, timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            {"url": data.get("video_url", ""), "width": width, "height": height, "format": "png"}
        ]

    def generate_shot_by_shot(self, shot_prompts, width=1080, height=1920, **kwargs) -> list[dict]:
        results = []
        for sp in shot_prompts:
            result = self.generate_video(
                prompt=sp.get("prompt", ""),
                negative_prompt=sp.get("negative_prompt", ""),
                duration=sp.get("duration", 5.0),
                width=width, height=height,
                reference_image=sp.get("reference_image"),
            )
            result["shot_id"] = sp.get("shot_id", len(results) + 1)
            results.append(result)
            time.sleep(kwargs.get("delay_between", 1.0))
        return results

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

    def upload_image(self, image_path: Path) -> str:
        """上传图片到火山引擎 (获取公网URL)"""
        if not image_path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")
        return self._prepare_image(str(image_path))

    # ================================================================
    # 下载 & 合并
    # ================================================================
    def _download_video(self, url: str, output_path: Path):
        import requests
        logger.info(f"[Jimeng ARK] 下载视频: {url[:80]}...")
        resp = requests.get(url, stream=True, timeout=600)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
        logger.info(f"[Jimeng ARK] 已保存: {output_path} ({output_path.stat().st_size} bytes)")

    def _merge_videos(self, video_paths: list[Path], output_path: Path):
        import subprocess
        concat_list = output_path.parent / "concat_list.txt"
        with open(concat_list, "w") as f:
            for vp in video_paths:
                f.write(f"file '{vp.resolve()}'\n")
        result = subprocess.run([
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", str(concat_list), "-c", "copy",
            str(output_path), "-y",
        ], capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"视频合并失败: {result.stderr[:300]}")
        logger.info(f"[Jimeng ARK] 视频合并完成: {output_path}")

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
