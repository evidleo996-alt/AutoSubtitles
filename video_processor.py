import os
import subprocess
import re
from typing import List, Dict, Optional


# 字幕烧录样式配置
FONT_SIZES = {"small": 18, "medium": 24, "large": 32}
POSITIONS = {"top": 8, "center": 10, "bottom": 2}  # ASS Alignment
COLORS = {
    "white": "&HFFFFFF",
    "yellow": "&H00FFFF",
    "cyan": "&HFFFF00"
}
BORDERS = {
    "outline": "OutlineColour=&H000000,Outline=2",
    "shadow": "Shadow=3,BackColour=&H80000000",
    "none": "Outline=0,Shadow=0"
}

class VideoProcessor:
    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    # Removed: detect_silence, detect_voice_activity, cut_video, cut_video_by_keep_segments
    # Since we only do simple transcoding/extraction now.

    def get_duration(self, input_file):
        cmd = [
            self.ffmpeg_path,
            "-i", input_file,
            "-hide_banner"
        ]
        try:
            result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
            duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})", result.stderr)
            if duration_match:
                h, m, s = map(float, duration_match.groups())
                return h * 3600 + m * 60 + s
        except Exception as e:
            print(f"Get duration failed: {e}")
        return 0.0

    def burn_subtitle(
        self,
        video_path: str,
        srt_path: str,
        output_path: Optional[str] = None,
        font_size: str = "medium",
        position: str = "bottom",
        color: str = "white",
        border: str = "outline"
    ) -> str:
        """
        将字幕烧录到视频中
        
        Args:
            video_path: 输入视频路径
            srt_path: SRT 字幕文件路径
            output_path: 输出视频路径，默认添加 _burned 后缀
            font_size: 字体大小 (small/medium/large)
            position: 字幕位置 (top/center/bottom)
            color: 字体颜色 (white/yellow/cyan)
            border: 边框样式 (outline/shadow/none)
        
        Returns:
            输出视频文件路径
        """
        if not output_path:
            base, ext = os.path.splitext(video_path)
            output_path = f"{base}_burned{ext}"
        
        # 构建样式字符串
        size = FONT_SIZES.get(font_size, 24)
        align = POSITIONS.get(position, 2)
        clr = COLORS.get(color, "&HFFFFFF")
        bdr = BORDERS.get(border, "Outline=2")
        
        # 处理字幕文件路径中的特殊字符
        srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        
        # ASS force_style 格式
        force_style = f"FontSize={size},Alignment={align},PrimaryColour={clr},{bdr}"
        
        # ffmpeg 命令
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-vf", f"subtitles='{srt_escaped}':force_style='{force_style}'",
            "-c:a", "copy",
            output_path
        ]
        
        try:
            print(f"开始烧录字幕: {video_path}")
            print(f"样式: {force_style}")
            result = subprocess.run(
                cmd,
                check=True,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"字幕烧录完成: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"字幕烧录失败: {e.stderr}")
            raise RuntimeError(f"字幕烧录失败: {e.stderr}")

if __name__ == "__main__":
    pass
