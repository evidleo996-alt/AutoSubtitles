"""数据库模块 - 使用连接池模式管理 SQLite 连接"""
import sqlite3
import json
import threading
from typing import Dict, Optional, Any
from datetime import datetime
from contextlib import contextmanager
from config import Config


class Database:
    """线程安全的数据库管理类"""
    
    _instance: Optional['Database'] = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = None):
        """单例模式确保只有一个数据库实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return
        self.db_path = str(db_path or Config.DB_PATH)
        self._local = threading.local()
        self._init_db()
        self._initialized = True

    @contextmanager
    def get_connection(self):
        """获取线程安全的数据库连接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.conn.row_factory = sqlite3.Row
        try:
            yield self._local.conn
            self._local.conn.commit()
        except Exception as e:
            self._local.conn.rollback()
            raise e

    def _init_db(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'pending',
                    message TEXT DEFAULT '',
                    progress INTEGER DEFAULT 0,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    data TEXT DEFAULT '{}'
                )
            ''')
            # 检查是否需要添加 progress 列（兼容旧数据库）
            cursor.execute("PRAGMA table_info(tasks)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'progress' not in columns:
                cursor.execute('ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0')

    def create_task(self, task_id: str, initial_data: Dict[str, Any]) -> None:
        """创建新任务"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute(
                """INSERT INTO tasks (id, status, message, progress, created_at, updated_at, data) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (task_id, "pending", "任务已创建", 0, now, now, json.dumps(initial_data))
            )

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, status, message, progress, data FROM tasks WHERE id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            
            if row:
                data = json.loads(row['data'])
                data.update({
                    "id": row['id'],
                    "status": row['status'],
                    "message": row['message'],
                    "progress": row['progress'] or 0
                })
                return data
            return None

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        message: Optional[str] = None,
        progress: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """更新任务状态和数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            
            updates = []
            params = []
            
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if message is not None:
                updates.append("message = ?")
                params.append(message)
            if progress is not None:
                updates.append("progress = ?")
                params.append(progress)
            if data is not None:
                cursor.execute("SELECT data FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()
                if row:
                    current_data = json.loads(row["data"] or "{}")
                    current_data.update(data)
                    updates.append("data = ?")
                    params.append(json.dumps(current_data))
            
            if not updates:
                return
                
            updates.append("updated_at = ?")
            params.append(now)
            params.append(task_id)
            
            sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

    def cleanup_old_tasks(self, days: int = 7) -> int:
        """清理超过指定天数的旧任务"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM tasks WHERE created_at < datetime('now', ?)",
                (f'-{days} days',)
            )
            return cursor.rowcount


# 全局数据库实例
db = Database()
