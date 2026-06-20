"""
TikTok AI Video Factory - Runway Provider (Gen-3/Gen-4)
支持: 图生视频 / 文生视频, 运动笔刷, 导演模式
"""

import logging
import time
from pathlib import Path
from typing import Optional

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class RunwayProvider(BaseProvider):
    provider_name = "runway"
    supports_text = False
    supports_image = False
    supports_vision = False
    supports_video = True

    API_BASE = "https://api.runwayml.com/v1"

    def _default_model(self) -> str:
        return "gen4"

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
        Runway视频生成

        支持模式:
          - text_to_video: 纯文本生成
          - image_to_video: 图生视频 (需提供reference_image)
          - director_mode: 导演模式 (需提供多张参考图)
        """
        if reference_image:
            return self._image_to_video(prompt, reference_image, duration, width, height, **kwargs)
        else:
            return self._text_to_video(prompt, negative_prompt, duration, width, height, **kwargs)

    def _text_to_video(self, prompt, negative_prompt, duration, width, height, **kwargs) -> dict:
        """文生视频"""
        # Runway Gen-3/4 支持5s和10s
        duration = 5 if duration <= 5 else 10

        payload = {
            "mode": "text_to_video",
            "prompt": prompt,
            "duration": duration,
            "resolution": f"{width}x{height}",
            "seed": kwargs.get("seed", -1),
        }

        try:
            resp = self.client.post(f"{self.API_BASE}/generate", json=payload, timeout=180)
            data = resp.json()
            task_id = data.get("id", "")

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
            logger.error(f"Runway生成失败: {e}")
            return self._mock_result(duration, width, height)

    def _image_to_video(self, prompt, reference_image, duration, width, height, **kwargs) -> dict:
        """图生视频 (Runway核心功能)"""
        duration = 5 if duration <= 5 else 10

        # 上传参考图片
        image_url = self._upload_image(reference_image)

        payload = {
            "mode": "image_to_video",
            "prompt": prompt,
            "image_url": image_url,
            "duration": duration,
            "motion_bucket_id": kwargs.get("motion_intensity", 127),
            "seed": kwargs.get("seed", -1),
        }

        try:
            resp = self.client.post(f"{self.API_BASE}/generate", json=payload, timeout=180)
            data = resp.json()
            task_id = data.get("id", "")

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
            logger.error(f"Runway图生视频失败: {e}")
            return self._mock_result(duration, width, height)

    # ================================================================
    # Runway特有: 导演模式
    # ================================================================
    def generate_director_mode(
        self,
        keyframes: list[dict],
        prompt: str,
        duration: float = 10.0,
        width: int = 1080,
        height: int = 1920,
        **kwargs,
    ) -> dict:
        """
        Runway导演模式: 多张关键帧控制镜头运动

        Args:
            keyframes: [
                {"image_path": "...", "position": 0.0},   # 起始帧
                {"image_path": "...", "position": 0.5},   # 中间帧
                {"image_path": "...", "position": 1.0},   # 结束帧
            ]
            prompt: 过渡描述
        """
        # 上传所有关键帧
        kf_data = []
        for kf in keyframes:
            url = self._upload_image(kf["image_path"])
            kf_data.append({"image_url": url, "position": kf["position"]})

        payload = {
            "mode": "director",
            "keyframes": kf_data,
            "prompt": prompt,
            "duration": duration,
            "resolution": f"{width}x{height}",
        }

        try:
            resp = self.client.post(f"{self.API_BASE}/generate", json=payload, timeout=300)
            data = resp.json()
            return {
                "url": data.get("video_url", ""),
                "task_id": data.get("id", ""),
                "duration": duration,
                "width": width,
                "height": height,
                "format": "mp4",
                "status": "processing",
            }
        except Exception as e:
            logger.error(f"Runway导演模式失败: {e}")
            return self._mock_result(duration, width, height)

    # ================================================================
    # 任务查询
    # ================================================================
    def query_task(self, task_id: str) -> dict:
        try:
            resp = self.client.get(f"{self.API_BASE}/tasks/{task_id}", timeout=15)
            data = resp.json()
            return {
                "task_id": task_id,
                "status": data.get("status", "unknown"),
                "result_url": data.get("video_url", ""),
                "progress": data.get("progress", 0),
            }
        except Exception:
            return {"task_id": task_id, "status": "error", "result_url": ""}

    # ================================================================
    # 辅助
    # ================================================================
    def _upload_image(self, image_path: str) -> str:
        """上传图片到Runway (获取临时URL)"""
        if image_path.startswith("http"):
            return image_path

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")

        try:
            with open(path, "rb") as f:
                resp = self.client.post(
                    f"{self.API_BASE}/upload",
                    files={"file": (path.name, f)},
                    timeout=30,
                )
            data = resp.json()
            return data.get("url", image_path)
        except Exception:
            # 上传失败时尝试base64
            import base64
            suffix = path.suffix.lower()
            mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
            mime = mime_map.get(suffix, "image/jpeg")
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime};base64,{data}"

    def _mock_result(self, duration, width, height) -> dict:
        return {
            "url": "",
            "task_id": f"runway_mock_{int(time.time())}",
            "duration": duration,
            "width": width,
            "height": height,
            "format": "mp4",
            "status": "pending",
        }
