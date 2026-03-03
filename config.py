"""
配置管理模块 - 集中管理所有配置项
"""
from pathlib import Path
from typing import Set


class Config:
    """应用配置类"""
    
    # 路径配置
    BASE_DIR: Path = Path(__file__).parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    ASSETS_DIR: Path = BASE_DIR / "assets"
    DB_PATH: Path = BASE_DIR / "tasks.db"
    
    # 文件上传配置
    ALLOWED_EXTENSIONS: Set[str] = {
        '.mp4', '.mov', '.avi', '.mkv', '.flv',  # 视频格式
        '.mp3', '.wav', '.m4a', '.aac',           # 音频格式
        '.srt'                                     # 字幕格式
    }
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB
    
    # Whisper 模型配置
    DEFAULT_MODEL_SIZE: str = "base"
    AVAILABLE_MODELS: tuple = ("tiny", "base", "small", "medium", "large")
    
    # LLM 默认配置
    LLM_PROVIDERS: dict = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-3.5-turbo"
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com",
            "default_model": "deepseek-chat"
        },
        "glm": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "default_model": "glm-4"
        },
        "aliyun": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-turbo"
        }
    }
    
    # 任务进度配置
    PROGRESS_STAGES: dict = {
        "init": 5,
        "audio_extract": 15,
        "whisper_start": 20,
        "whisper_done": 60,
        "llm_start": 70,
        "llm_done": 90,
        "note_start": 92,
        "note_done": 98,
        "complete": 100
    }
    
    @classmethod
    def ensure_dirs(cls) -> None:
        """确保必要的目录存在"""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def is_allowed_file(cls, filename: str) -> bool:
        """检查文件扩展名是否允许"""
        ext = Path(filename).suffix.lower()
        return ext in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def get_file_extension(cls, filename: str) -> str:
        """获取文件扩展名（小写）"""
        return Path(filename).suffix.lower()


# 创建默认配置实例
config = Config()
