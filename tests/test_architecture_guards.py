import unittest

from server import build_error_detail
from services.task_manager import TaskManager, TaskStatus


class ArchitectureGuardsTest(unittest.TestCase):
    def test_error_detail_schema(self):
        """验证统一错误结构包含 code 与 message。"""
        detail = build_error_detail("TASK_NOT_FOUND", "任务不存在")
        self.assertEqual(detail["code"], "TASK_NOT_FOUND")
        self.assertEqual(detail["message"], "任务不存在")

    def test_status_transition_rules(self):
        """验证任务状态机允许与禁止的流转规则。"""
        self.assertTrue(TaskManager.can_transition(TaskStatus.PENDING, TaskStatus.PROCESSING))
        self.assertTrue(TaskManager.can_transition(TaskStatus.PROCESSING, TaskStatus.COMPLETED))
        self.assertFalse(TaskManager.can_transition(TaskStatus.COMPLETED, TaskStatus.PROCESSING))
        self.assertFalse(TaskManager.can_transition(TaskStatus.FAILED, TaskStatus.PROCESSING))

    def test_progress_normalize(self):
        """验证进度归一化结果处于 0-100 区间。"""
        self.assertEqual(TaskManager._normalize_progress(-2), 0)
        self.assertEqual(TaskManager._normalize_progress(32), 32)
        self.assertEqual(TaskManager._normalize_progress(140), 100)


if __name__ == "__main__":
    unittest.main()
