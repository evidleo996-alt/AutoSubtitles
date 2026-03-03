"""工作流模块 - 处理字幕生成和LLM优化的完整流程"""
import os
import subprocess
from typing import Dict, Any, Optional

from services.task_manager import task_manager, TaskStatus
from video_processor import VideoProcessor
from subtitle_generator import SubtitleGenerator
from llm_helper import LLMSubtitleRefiner
from config import Config
from exceptions import AudioExtractionError, ProcessingError, LLMError

# 全局实例
video_processor = VideoProcessor()

# Whisper 模型缓存，避免重复加载
_generator_cache: Dict[str, SubtitleGenerator] = {}


def get_generator(model_size: str, progress_callback=None) -> SubtitleGenerator:
    """获取或创建 Whisper 生成器实例（带缓存）"""
    if model_size not in _generator_cache:
        generator = SubtitleGenerator(
            model_size=model_size,
            progress_callback=progress_callback
        )
        generator.load_model()
        _generator_cache[model_size] = generator
    else:
        # 更新回调函数
        _generator_cache[model_size].progress_callback = progress_callback
    return _generator_cache[model_size]


def run_simple_pipeline(task_id: str, options: Dict[str, Any]) -> None:
    """
    简化工作流: 视频/音频/字幕 -> 优化字幕 -> 小红书文案
    
    进度阶段:
    - 0-5%: 初始化
    - 5-15%: 音频提取
    - 15-60%: Whisper 转写
    - 60-90%: LLM 优化
    - 90-98%: 笔记生成
    - 100%: 完成
    """
    try:
        # 初始化
        task_manager.update_task_status(
            task_id, TaskStatus.PROCESSING, 
            "正在初始化任务...", 
            progress=Config.PROGRESS_STAGES["init"]
        )
        
        task_data = task_manager.get_task(task_id)
        if not task_data:
            raise ProcessingError("任务不存在")
        original_file = task_data.get("original_file")
        if not original_file:
            raise ProcessingError("缺少原始文件路径")
        base_name = os.path.splitext(original_file)[0]
        ext = os.path.splitext(original_file)[1].lower()
        
        raw_srt_path: Optional[str] = None
        
        # 分支 1: 输入是字幕文件 (.srt)
        if ext == ".srt":
            task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING,
                "检测到字幕文件，准备进行 LLM 优化...",
                progress=Config.PROGRESS_STAGES["whisper_done"]
            )
            raw_srt_path = original_file
            task_manager.update_task_data(task_id, {"srt_file": raw_srt_path})
            
        # 分支 2: 输入是媒体文件 (视频/音频)
        else:
            # 1. 提取音频
            audio_path = base_name + ".mp3"
            if ext in ['.mp3', '.wav', '.m4a', '.aac']:
                audio_path = original_file
                task_manager.update_task_status(
                    task_id, TaskStatus.PROCESSING,
                    "检测到音频文件，准备转写...",
                    progress=Config.PROGRESS_STAGES["audio_extract"]
                )
            else:
                task_manager.update_task_status(
                    task_id, TaskStatus.PROCESSING,
                    "正在从视频提取音频...",
                    progress=Config.PROGRESS_STAGES["audio_extract"]
                )
                cmd = [
                    "ffmpeg", "-y", "-i", original_file,
                    "-q:a", "0", "-map", "a",
                    audio_path
                ]
                try:
                    subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
                except subprocess.CalledProcessError as e:
                    error_msg = e.stderr.decode("utf-8", errors="ignore").strip()
                    raise AudioExtractionError(error_msg or "无法从视频中提取音频，请检查文件是否包含音轨。")
            
            task_manager.update_task_data(task_id, {"audio_file": audio_path})
            
            # 2. Whisper 转写
            model_size = options.get("model_size", Config.DEFAULT_MODEL_SIZE)
            task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING,
                f"正在使用 Whisper ({model_size}) 生成字幕...",
                progress=Config.PROGRESS_STAGES["whisper_start"]
            )
            
            def progress_callback(msg: str) -> None:
                """进度回调，根据消息更新进度"""
                # 根据消息内容估算进度
                progress = Config.PROGRESS_STAGES["whisper_start"]
                if "模型加载完成" in msg:
                    progress = 30
                elif "音频提取完成" in msg:
                    progress = 40
                elif "字幕生成完成" in msg:
                    progress = Config.PROGRESS_STAGES["whisper_done"]
                task_manager.update_task_status(
                    task_id, TaskStatus.PROCESSING, msg, progress=progress
                )
            
            generator = get_generator(model_size, progress_callback)
            generated_srt, _, _ = generator.generate_subtitle(audio_path, output_format="srt")
            raw_srt_path = generated_srt
            
            task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING,
                "字幕转写完成",
                progress=Config.PROGRESS_STAGES["whisper_done"]
            )
            task_manager.update_task_data(task_id, {"srt_file": raw_srt_path})
        
        # 3. LLM 优化 & 笔记生成 (可选)
        use_llm = options.get("use_llm", False)
        generate_note = options.get("generate_note", False)
        
        if use_llm:
            api_key = options.get("llm_api_key")
            base_url = options.get("llm_base_url")
            model = options.get("llm_model")
            humor_level = options.get("humor_level", "none")
            
            if not (api_key and base_url and model):
                raise LLMError("LLM 配置不完整", provider=model or "unknown")

            with open(raw_srt_path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            source_content = raw_content
            refiner = LLMSubtitleRefiner(
                api_key=api_key,
                base_url=base_url,
                model=model
            )

            task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING,
                f"正在使用 LLM ({model}) 优化字幕...",
                progress=Config.PROGRESS_STAGES["llm_start"]
            )

            try:
                optimized_content = refiner.optimize_subtitle(
                    raw_content,
                    humor_level=humor_level
                )
            except Exception as e:
                raise LLMError(f"LLM 字幕优化失败: {str(e)}", provider=model)

            optimized_srt_path = base_name + "_optimized.srt"
            with open(optimized_srt_path, "w", encoding="utf-8") as f:
                f.write(optimized_content)

            source_content = optimized_content if optimized_content else raw_content
            task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING,
                "LLM 字幕优化完成",
                progress=Config.PROGRESS_STAGES["llm_done"]
            )
            task_manager.update_task_data(task_id, {"optimized_srt_file": optimized_srt_path})

            if generate_note:
                task_manager.update_task_status(
                    task_id, TaskStatus.PROCESSING,
                    "正在生成小红书笔记文案...",
                    progress=Config.PROGRESS_STAGES["note_start"]
                )

                try:
                    note_content = refiner.generate_study_note(source_content)
                except Exception as e:
                    raise LLMError(f"LLM 笔记生成失败: {str(e)}", provider=model)

                note_path = base_name + "_xhs_note.md"
                with open(note_path, "w", encoding="utf-8") as f:
                    f.write(note_content)

                task_manager.update_task_status(
                    task_id, TaskStatus.PROCESSING,
                    "小红书笔记生成完成",
                    progress=Config.PROGRESS_STAGES["note_done"]
                )
                task_manager.update_task_data(task_id, {"note_file": note_path})

            task_manager.update_task_status(
                task_id, TaskStatus.PROCESSING,
                "正在生成内容摘要...",
                progress=96
            )

            try:
                summary_content = refiner.generate_summary(source_content)
            except Exception:
                summary_content = ""

            if summary_content and not summary_content.startswith("生成失败"):
                summary_path = base_name + "_summary.txt"
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(summary_content)
                task_manager.update_task_data(task_id, {
                    "summary_file": summary_path,
                    "summary_content": summary_content
                })
        
        # 完成
        task_manager.update_task_status(
            task_id, TaskStatus.COMPLETED,
            "处理完成！",
            progress=Config.PROGRESS_STAGES["complete"]
        )

    except AudioExtractionError as e:
        task_manager.update_task_status(
            task_id, TaskStatus.FAILED,
            f"音频提取失败: {e.message}"
        )
    except LLMError as e:
        task_manager.update_task_status(
            task_id, TaskStatus.FAILED,
            f"LLM 处理失败: {e.message}"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        task_manager.update_task_status(
            task_id, TaskStatus.FAILED,
            f"任务失败: {str(e)}"
        )
