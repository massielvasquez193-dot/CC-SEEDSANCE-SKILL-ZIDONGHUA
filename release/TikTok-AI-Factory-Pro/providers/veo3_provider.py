"""
TikTok AI Video Factory - VEO3 Provider (Google DeepMind)
支持: 完整视频生成，长视频模式(8s/15s/30s/60s)
"""

import logging
import time
from pathlib import Path
from typing import Optional

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class VEO3Provider(BaseProvider):
    provider_name = "veo3"
    supports_text = False
    supports_image = False
    supports_vision = False
    supports_video = True

    API_BASE = "https://api.veo3.google.com/v1"

    def _default_model(self) -> str:
        return "veo-3.0"

    def _create_client(self):
        import requests
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        return session

    def is_available(self) -> bool:
        return self.api_key is not None

    # ================================================================
    # 视频生成
    # ================================================================
    def _generate_video_impl(self, prompt, negative_prompt, duration, width, height, fps, reference_image, **kwargs) -> dict:
        """
        VEO3完整视频生成
        支持: 8s / 15s / 30s / 60s 四档
        """
        # VEO3 时长适配
        valid_durations = [8, 15, 30, 60]
        if duration not in valid_durations:
            closest = min(valid_durations, key=lambda x: abs(x - duration))
            logger.info(f"VEO3时长 {duration}s → 适配为 {closest}s")
            duration = closest

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "duration_seconds": duration,
            "aspect_ratio": "9:16" if height > width else "16:9" if width > height else "1:1",
            "resolution": f"{width}x{height}",
            "fps": fps,
            "camera_control": kwargs.get("camera_control", "cinematic"),
            "motion_intensity": kwargs.get("motion_intensity", 0.5),
            "seed": kwargs.get("seed", -1),
        }

        try:
            resp = self.client.post(f"{self.API_BASE}/generate", json=payload, timeout=300)
            data = resp.json()
            task_id = data.get("task_id", "")

            return {
                "url": data.get("video_url", ""),
                "task_id": task_id,
                "duration": duration,
                "width": width,
                "height": height,
                "format": "mp4",
                "status": "processing" if task_id else "completed",
            }
        except Exception as e:
            logger.error(f"VEO3生成失败: {e}")
            return self._mock_result(duration, width, height)

    # ================================================================
    # VEO3特有: 多时长生成
    # ================================================================
    def generate_multi_duration(
        self,
        prompt: str,
        negative_prompt: str = None,
        durations: list[int] = None,
        width: int = 1080,
        height: int = 1920,
        **kwargs,
    ) -> dict[int, dict]:
        """
        同时生成多个时长的版本

        Returns:
            {8: {...}, 15: {...}, 30: {...}, 60: {...}}
        """
        if durations is None:
            durations = [8, 15]

        results = {}
        for dur in durations:
            logger.info(f"VEO3生成 {dur}s 版本...")
            results[dur] = self.generate_video(
                prompt=prompt,
                negative_prompt=negative_prompt,
                duration=dur,
                width=width,
                height=height,
                **kwargs,
            )
            time.sleep(kwargs.get("delay_between", 1.0))

        return results

    # ================================================================
    # 任务查询
    # ================================================================
    def query_task(self, task_id: str) -> dict:
        try:
            resp = self.client.get(f"{self.API_BASE}/task/{task_id}", timeout=15)
            data = resp.json()
            return {
                "task_id": task_id,
                "status": data.get("status", "unknown"),
                "result_url": data.get("video_url", ""),
                "progress": data.get("progress", 0),
            }
        except Exception as e:
            logger.error(f"查询VEO3任务失败: {e}")
            return {"task_id": task_id, "status": "error", "result_url": ""}

    def _mock_result(self, duration, width, height) -> dict:
        return {
            "url": "",
            "task_id": f"veo3_mock_{int(time.time())}",
            "duration": duration,
            "width": width,
            "height": height,
            "format": "mp4",
            "status": "pending",
            "note": "VEO3 API不可用，此为占位结果。",
        }
