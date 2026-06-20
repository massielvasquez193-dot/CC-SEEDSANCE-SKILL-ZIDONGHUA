"""
TikTok AI Video Factory - Kling (可灵) Provider
支持: 图生视频 / 文生视频, 运镜控制, 高画质模式
"""

import logging
import time
from pathlib import Path
from typing import Optional

from providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class KlingProvider(BaseProvider):
    provider_name = "kling"
    supports_text = False
    supports_image = False
    supports_vision = False
    supports_video = True

    API_BASE = "https://api.kling.ai/v1"

    def _default_model(self) -> str:
        return "kling-v2"

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
        可灵视频生成
        特色: 运镜控制、高画质模式、图生视频
        """
        if reference_image:
            return self._image_to_video(prompt, reference_image, duration, width, height, fps, **kwargs)
        else:
            return self._text_to_video(prompt, negative_prompt, duration, width, height, fps, **kwargs)

    def _text_to_video(self, prompt, negative_prompt, duration, width, height, fps, **kwargs) -> dict:
        """文生视频"""
        # Kling支持5s和10s
        duration = 5 if duration <= 5 else 10

        payload = {
            "model": self.model,
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "duration": duration,
            "size": f"{width}x{height}",
            "mode": kwargs.get("mode", "std"),  # std / pro
            "camera_control": kwargs.get("camera_control", None),
            "seed": kwargs.get("seed", -1),
        }

        # 运镜控制 (Kling特有)
        camera = kwargs.get("camera_control")
        if camera:
            payload["camera_control"] = camera  # {"type": "push_in", "strength": 0.5}

        try:
            resp = self.client.post(f"{self.API_BASE}/videos/text2video", json=payload, timeout=180)
            data = resp.json()
            task_id = data.get("data", {}).get("task_id", "")

            return {
                "url": "",
                "task_id": task_id,
                "duration": duration,
                "width": width,
                "height": height,
                "format": "mp4",
                "status": "processing",
            }
        except Exception as e:
            logger.error(f"Kling生成失败: {e}")
            return self._mock_result(duration, width, height)

    def _image_to_video(self, prompt, reference_image, duration, width, height, fps, **kwargs) -> dict:
        """图生视频 (可灵核心功能)"""
        duration = 5 if duration <= 5 else 10

        image_url = self._prepare_image(reference_image)

        payload = {
            "model": self.model,
            "image_url": image_url,
            "prompt": prompt,
            "duration": duration,
            "mode": kwargs.get("mode", "std"),
            "camera_control": kwargs.get("camera_control", None),
        }

        try:
            resp = self.client.post(f"{self.API_BASE}/videos/image2video", json=payload, timeout=180)
            data = resp.json()
            task_id = data.get("data", {}).get("task_id", "")

            return {
                "url": "",
                "task_id": task_id,
                "duration": duration,
                "width": width,
                "height": height,
                "format": "mp4",
                "status": "processing",
            }
        except Exception as e:
            logger.error(f"Kling图生视频失败: {e}")
            return self._mock_result(duration, width, height)

    # ================================================================
    # Kling特有: 运镜控制
    # ================================================================
    CAMERA_MOVEMENTS = {
        "push_in": {"type": "push_in", "description": "推近"},
        "pull_out": {"type": "pull_out", "description": "拉远"},
        "pan_left": {"type": "pan_left", "description": "左摇"},
        "pan_right": {"type": "pan_right", "description": "右摇"},
        "tilt_up": {"type": "tilt_up", "description": "上摇"},
        "tilt_down": {"type": "tilt_down", "description": "下摇"},
        "zoom_in": {"type": "zoom_in", "description": "变焦推"},
        "zoom_out": {"type": "zoom_out", "description": "变焦拉"},
        "rotate": {"type": "rotate", "description": "旋转"},
        "tracking": {"type": "tracking", "description": "跟随"},
        "static": {"type": "static", "description": "固定"},
    }

    def generate_with_camera(
        self,
        prompt: str,
        reference_image: str = None,
        camera_type: str = "push_in",
        camera_strength: float = 0.5,
        duration: float = 5.0,
        mode: str = "pro",
        **kwargs,
    ) -> dict:
        """
        带运镜控制的视频生成

        Args:
            camera_type: push_in/pull_out/pan_left/pan_right/tilt_up/tilt_down/zoom_in/zoom_out/rotate/tracking/static
            camera_strength: 运镜强度 0.0-1.0
            mode: std(标准)/pro(高画质)
        """
        camera_control = {
            "type": camera_type,
            "strength": camera_strength,
        }

        return self.generate_video(
            prompt=prompt,
            reference_image=reference_image,
            duration=duration,
            mode=mode,
            camera_control=camera_control,
            **kwargs,
        )

    # ================================================================
    # 任务查询
    # ================================================================
    def query_task(self, task_id: str) -> dict:
        try:
            resp = self.client.get(f"{self.API_BASE}/tasks/{task_id}", timeout=15)
            data = resp.json()
            task_data = data.get("data", {})

            status = task_data.get("status", "unknown")
            result = {
                "task_id": task_id,
                "status": status,
                "result_url": "",
                "progress": task_data.get("progress", 0),
            }

            if status == "completed":
                result["result_url"] = task_data.get("video_url", "")

            return result
        except Exception:
            return {"task_id": task_id, "status": "error", "result_url": ""}

    # ================================================================
    # 辅助
    # ================================================================
    def _prepare_image(self, image_path: str) -> str:
        if image_path.startswith(("http://", "https://")):
            return image_path

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")

        import base64
        suffix = path.suffix.lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
        mime = mime_map.get(suffix, "image/jpeg")

        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{data}"

    def _mock_result(self, duration, width, height) -> dict:
        return {
            "url": "",
            "task_id": f"kling_mock_{int(time.time())}",
            "duration": duration,
            "width": width,
            "height": height,
            "format": "mp4",
            "status": "pending",
        }
