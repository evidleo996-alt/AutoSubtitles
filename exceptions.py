"""
自定义异常模块 - 统一错误处理
"""
from typing import Optional


class AppException(Exception):
    """应用基础异常类"""
    
    def __init__(self, message: str, code: str = "ERROR", details: Optional[str] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """转换为字典格式，便于 API 响应"""
        result = {
            "code": self.code,
            "message": self.message
        }
        if self.details:
            result["details"] = self.details
        return result


class FileValidationError(AppException):
    """文件验证错误"""
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message, code="FILE_VALIDATION_ERROR", details=details)


class FileSizeError(FileValidationError):
    """文件大小超限错误"""
    
    def __init__(self, max_size_mb: int):
        super().__init__(
            message=f"文件大小超过限制 ({max_size_mb}MB)",
            details=f"请上传小于 {max_size_mb}MB 的文件"
        )


class FileTypeError(FileValidationError):
    """文件类型不支持错误"""
    
    def __init__(self, ext: str, allowed: list):
        super().__init__(
            message=f"不支持的文件类型: {ext}",
            details=f"支持的格式: {', '.join(allowed)}"
        )


class ProcessingError(AppException):
    """处理过程错误"""
    
    def __init__(self, message: str, stage: Optional[str] = None):
        details = f"发生在阶段: {stage}" if stage else None
        super().__init__(message, code="PROCESSING_ERROR", details=details)


class AudioExtractionError(ProcessingError):
    """音频提取错误"""
    
    def __init__(self, message: str = "无法从视频中提取音频"):
        super().__init__(message, stage="音频提取")


class TranscriptionError(ProcessingError):
    """语音转写错误"""
    
    def __init__(self, message: str = "语音识别失败"):
        super().__init__(message, stage="Whisper转写")


class LLMError(AppException):
    """LLM 相关错误"""
    
    def __init__(self, message: str, provider: Optional[str] = None):
        details = f"LLM 提供商: {provider}" if provider else None
        super().__init__(message, code="LLM_ERROR", details=details)


class LLMConfigError(LLMError):
    """LLM 配置错误"""
    
    def __init__(self, missing_field: str):
        super().__init__(
            message=f"LLM 配置不完整: 缺少 {missing_field}",
            provider=None
        )


class LLMAPIError(LLMError):
    """LLM API 调用错误"""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message, provider=provider)


class TaskNotFoundError(AppException):
    """任务不存在错误"""
    
    def __init__(self, task_id: str):
        super().__init__(
            message=f"任务不存在: {task_id}",
            code="TASK_NOT_FOUND"
        )


class FileNotFoundError(AppException):
    """文件不存在错误"""
    
    def __init__(self, file_type: str):
        super().__init__(
            message=f"请求的文件不存在: {file_type}",
            code="FILE_NOT_FOUND"
        )
