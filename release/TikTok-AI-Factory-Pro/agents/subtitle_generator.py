"""
TikTok AI Video Factory - 字幕生成Agent
根据脚本生成SRT格式字幕文件
"""

import logging
import re
from datetime import datetime

from prompts.system_prompts import SUBTITLE_PROMPT

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """SRT字幕生成器"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def generate(self, script: str) -> str:
        """根据脚本生成SRT字幕"""
        logger.info("生成SRT字幕...")

        if self.ai_client:
            return self._ai_generate(script)
        else:
            return self._parse_and_generate(script)

    def _ai_generate(self, script: str) -> str:
        """AI驱动生成字幕"""
        try:
            prompt = SUBTITLE_PROMPT.format(script=script)
            return prompt
        except Exception as e:
            logger.error(f"AI字幕生成失败: {e}")
            return self._parse_and_generate(script)

    def _parse_and_generate(self, script: str) -> str:
        """从脚本解析并生成SRT字幕"""
        # 提取字幕内容
        subtitle_pattern = re.findall(r'\[字幕\]\s*\n(.*?)(?:\n\n|\n\[|$)', script, re.DOTALL)
        voiceover_pattern = re.findall(r'\[口播文案\]\s*\n(.*?)(?:\n\n|\n\[|$)', script, re.DOTALL)

        # 提取时长信息
        duration_match = re.search(r'时长[：:]\s*(\d+)', script)
        total_duration = int(duration_match.group(1)) if duration_match else 15

        # 提取各段时间点
        time_matches = re.findall(r'\((\d+)[-~](\d+)秒?\)', script)

        subtitles = []
        if subtitle_pattern:
            subtitles = [s.strip().strip('"') for s in subtitle_pattern]
        elif voiceover_pattern:
            subtitles = [v.strip().strip('"') for v in voiceover_pattern]
        else:
            # 从脚本中手动提取
            subtitles = self._extract_subtitles_heuristic(script)

        return self._format_srt(subtitles, total_duration, time_matches)

    def _extract_subtitles_heuristic(self, script: str) -> list[str]:
        """启发式提取字幕"""
        default_subtitles = [
            "🔥 发现了一个宝藏产品！",
            "你是不是也遇到过这种问题？",
            "之前试过好多产品都没用",
            "直到我发现了这个宝藏！",
            "你看这个质感，颜值也太高了吧",
            "效果真的太惊艳了！",
            "赶紧去试试吧！",
            "链接我放在主页了",
            "现在下单还有限时优惠！",
        ]

        # 尝试从脚本中提取引号内的文字
        quoted = re.findall(r'"([^"]*)"', script)
        if quoted:
            return quoted[:len(default_subtitles)]

        return default_subtitles

    def _format_srt(self, subtitles: list[str], total_duration: int, time_matches: list = None) -> str:
        """格式化为SRT格式"""
        if not subtitles:
            return ""

        srt_entries = []
        segment_count = len(subtitles)
        segment_duration = total_duration / segment_count

        for i, text in enumerate(subtitles):
            start_sec = i * segment_duration
            end_sec = min((i + 1) * segment_duration, total_duration)

            # 格式化时间戳
            start_ts = self._format_timestamp(start_sec)
            end_ts = self._format_timestamp(end_sec)

            # 中文字幕每行不超过20字
            lines = self._split_chinese_text(text, max_chars=20)

            entry = f"{i+1}\n{start_ts} --> {end_ts}\n{lines}\n"
            srt_entries.append(entry)

        return "\n".join(srt_entries)

    def _format_timestamp(self, seconds: float) -> str:
        """格式化时间戳为 SRT 格式 HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _split_chinese_text(self, text: str, max_chars: int = 20) -> str:
        """分割中文文本为多行"""
        text = text.strip()
        if len(text) <= max_chars:
            return text

        # 在标点处分割
        lines = []
        current = ""
        for char in text:
            current += char
            if len(current) >= max_chars or char in "，。！？、；：":
                lines.append(current)
                current = ""
        if current:
            lines.append(current)

        return "\n".join(lines[:2])  # 最多两行

    def generate_bilingual(self, script: str, target_lang: str = "en") -> str:
        """生成双语字幕"""
        cn_srt = self.generate(script)
        # 简单双语处理：中英交替
        # 完整实现需要翻译API
        return cn_srt

    def save_srt(self, srt_content: str, output_path) -> None:
        """保存SRT文件"""
        from pathlib import Path
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        logger.info(f"字幕已保存: {path}")
