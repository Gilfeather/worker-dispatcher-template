import pytest
from app.domain.enums import TaskStatus, TaskPriority, WorkerStatus


class TestTaskStatus:
    def test_task_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.RETRY.value == "retry"
    
    def test_task_status_enum_members(self):
        expected_members = {
            "PENDING", "IN_PROGRESS", "COMPLETED", 
            "FAILED", "CANCELLED", "RETRY"
        }
        actual_members = {member.name for member in TaskStatus}
        assert actual_members == expected_members


class TestTaskPriority:
    def test_task_priority_values(self):
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"
    
    def test_task_priority_enum_members(self):
        expected_members = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        actual_members = {member.name for member in TaskPriority}
        assert actual_members == expected_members


class TestWorkerStatus:
    def test_worker_status_values(self):
        assert WorkerStatus.IDLE.value == "idle"
        assert WorkerStatus.BUSY.value == "busy"
        assert WorkerStatus.OFFLINE.value == "offline"
        assert WorkerStatus.MAINTENANCE.value == "maintenance"
    
    def test_worker_status_enum_members(self):
        expected_members = {"IDLE", "BUSY", "OFFLINE", "MAINTENANCE"}
        actual_members = {member.name for member in WorkerStatus}
        assert actual_members == expected_members