"""任务管理模块 - 统一管理任务状态和进度"""
from typing import Dict, Any, Optional
from database import db
import uuid


class TaskStatus:
    """任务状态常量"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_EDIT = "waiting_for_edit"
    WAITING_FOR_TEXT_EDIT = "waiting_for_text_edit"


class TaskManager:
    """任务管理器"""

    ALLOWED_TRANSITIONS = {
        TaskStatus.PENDING: {TaskStatus.PROCESSING, TaskStatus.FAILED},
        TaskStatus.PROCESSING: {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.WAITING_FOR_EDIT,
            TaskStatus.WAITING_FOR_TEXT_EDIT
        },
        TaskStatus.WAITING_FOR_EDIT: {TaskStatus.PROCESSING, TaskStatus.FAILED},
        TaskStatus.WAITING_FOR_TEXT_EDIT: {TaskStatus.PROCESSING, TaskStatus.FAILED},
        TaskStatus.COMPLETED: set(),
        TaskStatus.FAILED: set()
    }

    @staticmethod
    def _normalize_progress(progress: Optional[int]) -> Optional[int]:
        if progress is None:
            return None
        return max(0, min(100, int(progress)))

    @staticmethod
    def can_transition(from_status: str, to_status: str) -> bool:
        if from_status == to_status:
            return True
        allowed = TaskManager.ALLOWED_TRANSITIONS.get(from_status, set())
        return to_status in allowed
    
    @staticmethod
    def create_task(original_file: str) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        initial_data = {
            "original_file": original_file,
            "video_file": original_file,
            "steps": []
        }
        db.create_task(task_id, initial_data)
        return task_id

    @staticmethod
    def get_task(task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return db.get_task(task_id)

    @staticmethod
    def update_task_status(
        task_id: str,
        status: str,
        message: Optional[str] = None,
        progress: Optional[int] = None
    ) -> None:
        """更新任务状态和进度"""
        task = db.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        current_status = task.get("status", TaskStatus.PENDING)
        if not TaskManager.can_transition(current_status, status):
            raise ValueError(f"非法状态流转: {current_status} -> {status}")
        db.update_task(
            task_id,
            status=status,
            message=message,
            progress=TaskManager._normalize_progress(progress)
        )

    @staticmethod
    def update_task_data(task_id: str, data: Dict[str, Any]) -> None:
        """更新任务数据"""
        db.update_task(task_id, data=data)

    @staticmethod
    def update_progress(task_id: str, progress: int, message: Optional[str] = None) -> None:
        """仅更新进度"""
        db.update_task(
            task_id,
            progress=TaskManager._normalize_progress(progress),
            message=message
        )

    @staticmethod
    def get_all_tasks() -> list:
        """获取所有任务（未实现）"""
        return []


# 全局任务管理器实例
task_manager = TaskManager()
