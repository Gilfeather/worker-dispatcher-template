import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.domain.entities import Task, Worker, TaskResult, TaskId, WorkerId
from app.domain.enums import TaskStatus, TaskPriority, WorkerStatus


class TestTask:
    def test_task_creation(self):
        task = Task(name="Test Task")
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert isinstance(task.created_at, datetime)

    def test_task_can_retry(self):
        task = Task(name="Test Task", max_retries=3)
        assert task.can_retry() is True

        task.retry_count = 2
        assert task.can_retry() is True

        task.retry_count = 3
        assert task.can_retry() is False

    def test_task_increment_retry(self):
        task = Task(name="Test Task")
        initial_count = task.retry_count
        task.increment_retry()
        assert task.retry_count == initial_count + 1

    def test_task_is_completed(self):
        task = Task(name="Test Task")

        task.status = TaskStatus.PENDING
        assert task.is_completed() is False

        task.status = TaskStatus.IN_PROGRESS
        assert task.is_completed() is False

        task.status = TaskStatus.COMPLETED
        assert task.is_completed() is True

        task.status = TaskStatus.FAILED
        assert task.is_completed() is True

        task.status = TaskStatus.CANCELLED
        assert task.is_completed() is True

    def test_task_should_execute_no_schedule(self):
        task = Task(name="Test Task")
        assert task.should_execute() is True

    def test_task_should_execute_with_schedule(self):
        task = Task(name="Test Task")

        # Schedule for future
        task.scheduled_at = datetime.now() + timedelta(hours=1)
        assert task.should_execute() is False

        # Schedule for past
        task.scheduled_at = datetime.now() - timedelta(hours=1)
        assert task.should_execute() is True

    def test_task_validation(self):
        # Test empty name validation
        with pytest.raises(ValueError, match="Task name cannot be empty"):
            Task(name="   ")

        # Test negative max_retries validation
        with pytest.raises(ValueError, match="Max retries cannot be negative"):
            Task(name="Test Task", max_retries=-1)


class TestWorker:
    def test_worker_creation(self):
        worker = Worker(name="Test Worker")
        assert worker.name == "Test Worker"
        assert worker.status == WorkerStatus.IDLE
        assert worker.capabilities == []
        assert worker.current_task is None
        assert isinstance(worker.last_heartbeat, datetime)

    def test_worker_is_available(self):
        worker = Worker(name="Test Worker")

        worker.status = WorkerStatus.IDLE
        assert worker.is_available() is True

        worker.status = WorkerStatus.BUSY
        assert worker.is_available() is False

        worker.status = WorkerStatus.OFFLINE
        assert worker.is_available() is False

    def test_worker_assign_task(self):
        worker = Worker(name="Test Worker")
        task_id = TaskId()

        worker.assign_task(task_id)
        assert worker.current_task == task_id
        assert worker.status == WorkerStatus.BUSY

    def test_worker_complete_task(self):
        worker = Worker(name="Test Worker")
        task_id = TaskId()

        worker.assign_task(task_id)
        worker.complete_task()

        assert worker.current_task is None
        assert worker.status == WorkerStatus.IDLE

    def test_worker_update_heartbeat(self):
        worker = Worker(name="Test Worker")
        old_heartbeat = worker.last_heartbeat

        # Wait a bit to ensure time difference
        import time

        time.sleep(0.01)

        worker.update_heartbeat()
        assert worker.last_heartbeat > old_heartbeat

    def test_worker_is_healthy(self):
        worker = Worker(name="Test Worker")

        # Fresh worker should be healthy
        assert worker.is_healthy() is True

        # Old heartbeat should be unhealthy
        worker.last_heartbeat = datetime.now() - timedelta(seconds=60)
        assert worker.is_healthy(timeout_seconds=30) is False

    def test_worker_validation(self):
        # Test empty name validation
        with pytest.raises(ValueError, match="Worker name cannot be empty"):
            Worker(name="   ")


class TestTaskResult:
    def test_task_result_creation(self):
        task_id = TaskId()
        worker_id = WorkerId()

        result = TaskResult(
            task_id=task_id, worker_id=worker_id, status=TaskStatus.COMPLETED
        )

        assert result.task_id == task_id
        assert result.worker_id == worker_id
        assert result.status == TaskStatus.COMPLETED
        assert result.result_data is None
        assert result.error_message is None
        assert isinstance(result.completed_at, datetime)

    def test_task_result_is_success(self):
        task_id = TaskId()
        worker_id = WorkerId()

        result = TaskResult(
            task_id=task_id, worker_id=worker_id, status=TaskStatus.COMPLETED
        )
        assert result.is_success() is True

        result.status = TaskStatus.FAILED
        assert result.is_success() is False

    def test_task_result_is_failure(self):
        task_id = TaskId()
        worker_id = WorkerId()

        result = TaskResult(
            task_id=task_id, worker_id=worker_id, status=TaskStatus.FAILED
        )
        assert result.is_failure() is True

        result.status = TaskStatus.COMPLETED
        assert result.is_failure() is False


class TestTaskId:
    def test_task_id_creation(self):
        task_id = TaskId()
        assert task_id.value is not None
        assert isinstance(task_id.value, type(uuid4()))

    def test_task_id_string_representation(self):
        task_id = TaskId()
        assert str(task_id) == str(task_id.value)


class TestWorkerId:
    def test_worker_id_creation(self):
        worker_id = WorkerId()
        assert worker_id.value is not None
        assert isinstance(worker_id.value, type(uuid4()))

    def test_worker_id_string_representation(self):
        worker_id = WorkerId()
        assert str(worker_id) == str(worker_id.value)
