import os
import whisper
import warnings
import shutil
import subprocess
from typing import Optional, Callable, Tuple, List, Dict, Any

# Suppress warnings from whisper if any
warnings.filterwarnings("ignore")

class SubtitleGenerator:
    def __init__(self, model_size: str = "base", progress_callback: Optional[Callable[[str], None]] = None):
        """
        初始化字幕生成器
        :param model_size: Whisper 模型大小 (tiny, base, small, medium, large)
        :param progress_callback: 进度回调函数，接收字符串消息
        """
        if not shutil.which("ffmpeg"):
            error_msg = (
                "未找到 ffmpeg 组件，这是处理视频所必需的。\n"
                "请按照以下步骤安装：\n"
                "1. 打开终端 (Terminal)\n"
                "2. 输入命令: brew install ffmpeg\n"
                "   (如果您没有安装 Homebrew，请访问 brew.sh)\n"
                "或者联系您的技术支持。"
            )
            raise RuntimeError(error_msg)
            
        self.model_size = model_size
        self.progress_callback = progress_callback
        self.model = None

    def log(self, message: str):
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)

    def load_model(self):
        """加载 Whisper 模型，并处理可能的缓存错误"""
        self.log(f"正在加载 Whisper 模型 ({self.model_size})...")
        try:
            self.model = whisper.load_model(self.model_size)
            self.log("模型加载完成")
        except RuntimeError as e:
            if "checksum" in str(e).lower() or "sha256" in str(e).lower():
                self.log("模型文件校验失败，正在清除缓存并重试...")
                self._clear_whisper_cache()
                self.model = whisper.load_model(self.model_size)
                self.log("模型重新下载并加载完成")
            else:
                self.log(f"模型加载失败: {str(e)}")
                raise
        except Exception as e:
            self.log(f"模型加载失败: {str(e)}")
            raise

    def _clear_whisper_cache(self):
        """清理 Whisper 模型缓存"""
        cache_dir = os.path.expanduser("~/.cache/whisper")
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                self.log(f"已清理缓存目录: {cache_dir}")
            except Exception as e:
                self.log(f"清理缓存失败: {e}")

    def generate_subtitle(self, video_path: str, output_format: str = "srt"):
        """
        生成字幕文件，并提取音频
        :return: (subtitle_path, audio_path, word_segments)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件未找到: {video_path}")

        if not self.model:
            self.load_model()

        self.log(f"开始转写视频: {os.path.basename(video_path)}")
        
        # 始终提取音频文件，供用户下载
        # 命名为：视频文件名_audio.mp3
        audio_path = os.path.splitext(video_path)[0] + "_audio.mp3"
        temp_audio_needed = False # 标记是否是为了 Whisper 临时提取的（如果是临时提取且不是最终音频，则需清理）

        # 检查是否已经存在同名音频文件，避免重复提取
        if not os.path.exists(audio_path):
            self.log("正在提取音频文件...")
            try:
                # 使用 ffmpeg 提取音频 (128k mp3 足够清晰且体积适中)
                subprocess.run([
                    "ffmpeg", "-y", "-i", video_path, 
                    "-vn", "-acodec", "libmp3lame", "-q:a", "2", 
                    audio_path
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.log("音频提取完成")
            except Exception as e:
                self.log(f"音频提取失败: {e}，将尝试直接使用视频文件进行识别")
                # 如果提取失败，audio_path 回退到视频路径，但这样用户就无法下载音频了
                # 这里为了流程继续，我们回退，但在返回值里可能 audio_path 会是视频路径或者 None
                audio_path = video_path

        # 识别使用的路径 (通常就是提取出来的 audio_path)
        transcribe_input = audio_path

        try:
            # 使用 Whisper 进行转写，启用 word_timestamps
            result = self.model.transcribe(
                transcribe_input, 
                verbose=False, 
                language='zh', 
                initial_prompt="以下是普通话的字幕。",
                word_timestamps=True
            )
        except Exception as e:
            raise e
        
        output_path = os.path.splitext(video_path)[0] + "." + output_format
        
        if output_format == "srt":
            self._save_srt(result["segments"], output_path)
        
        self.log(f"字幕生成完成: {output_path}")
        
        # 返回字幕路径和音频路径
        # 如果 audio_path 就是 video_path (说明提取失败)，则返回 None 以告知无法下载音频
        final_audio_path = audio_path if audio_path != video_path else None
        
        # 提取 segment 信息供后续处理 (Text-Based Editing)
        # result["segments"] 包含 [{'id': 0, 'seek': 0, 'start': 0.0, 'end': 2.0, 'text': '...', 'words': [...]}, ...]
        return output_path, final_audio_path, result["segments"]

    def _save_srt(self, segments, output_path):
        """保存为 SRT 格式"""
        with open(output_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments):
                start = self._format_timestamp(segment["start"])
                end = self._format_timestamp(segment["end"])
                text = segment["text"].strip()
                
                f.write(f"{i + 1}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")

    @staticmethod
    def _format_timestamp(seconds: float):
        """将秒数转换为 SRT 时间戳格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

if __name__ == "__main__":
    # 测试代码
    generator = SubtitleGenerator(model_size="base")
    # generator.generate_subtitle("path/to/video.mp4")
