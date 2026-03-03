import os
import requests
import random
import subprocess
from typing import List, Optional

class BRollGenerator:
    def __init__(self, pexels_api_key: str, ffmpeg_path="ffmpeg"):
        self.api_key = pexels_api_key
        self.ffmpeg_path = ffmpeg_path
        self.headers = {"Authorization": self.api_key}

    def search_video(self, query: str, orientation: str = "landscape") -> Optional[str]:
        """
        在 Pexels 搜索视频并返回下载链接
        :param query: 搜索关键词 (英文)
        :param orientation: landscape, portrait, square
        """
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=5&orientation={orientation}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data["videos"]:
                    # 随机选择一个视频
                    video = random.choice(data["videos"])
                    # 选择最高质量的视频文件链接
                    video_files = video["video_files"]
                    # 优先找 HD 质量
                    best_file = next((f for f in video_files if f["width"] >= 1280), video_files[0])
                    return best_file["link"]
        except Exception as e:
            print(f"Pexels search error: {e}")
        return None

    def download_video(self, url: str, output_path: str):
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return True
        except Exception as e:
            print(f"Download error: {e}")
            return False

    def overlay_broll(self, base_video: str, broll_video: str, output_path: str, start_time: float, duration: float):
        """
        将 B-Roll 覆盖到基础视频的指定时间段 (保持原音频)
        """
        # complex filter:
        # [1:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1[broll];
        # [0:v][broll]overlay=enable='between(t,start,end)'[outv]
        
        # 注意：这里简化处理，假设视频都是 1080p。实际生产需要探测分辨率。
        # 另外，broll 需要 trim 到指定 duration，并且 loop (如果不够长) 或者 speed up?
        # 简单起见：假设 broll 足够长，或者我们只截取前 duration 秒。
        
        cmd = [
            self.ffmpeg_path,
            "-i", base_video,
            "-i", broll_video,
            "-filter_complex", 
            f"[1:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,trim=duration={duration}[broll];[0:v][broll]overlay=enable='between(t,{start_time},{start_time+duration})':eof_action=pass[outv]",
            "-map", "[outv]",
            "-map", "0:a",
            "-c:a", "copy",
            "-y", output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"B-Roll overlay error: {e}")
            return False
