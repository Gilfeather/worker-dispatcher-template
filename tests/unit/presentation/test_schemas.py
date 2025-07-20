import pytest
from datetime import datetime
from pydantic import ValidationError

from app.presentation.logic.schemas import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    WorkerCreateRequest,
    WorkerUpdateRequest,
    WorkerResponse,
    TaskResultResponse,
    WorkerHeartbeatRequest,
    TaskAssignmentRequest,
    TaskCompletionRequest,
    TaskFailureRequest,
)
from app.domain.enums import TaskStatus, TaskPriority, WorkerStatus


class TestTaskCreateRequest:
    def test_valid_task_create_request(self):
        request = TaskCreateRequest(
            name="Test Task",
            priority=TaskPriority.HIGH,
            payload={"key": "value"},
            max_retries=5,
        )

        assert request.name == "Test Task"
        assert request.priority == TaskPriority.HIGH
        assert request.payload == {"key": "value"}
        assert request.max_retries == 5

    def test_task_create_request_defaults(self):
        request = TaskCreateRequest(name="Test Task")

        assert request.name == "Test Task"
        assert request.priority == TaskPriority.MEDIUM
        assert request.payload == {}
        assert request.scheduled_at is None
        assert request.max_retries == 3

    def test_task_create_request_validation(self):
        # Test empty name
        with pytest.raises(ValidationError):
            TaskCreateRequest(name="")

        # Test negative max_retries
        with pytest.raises(ValidationError):
            TaskCreateRequest(name="Test Task", max_retries=-1)

        # Test max_retries too high
        with pytest.raises(ValidationError):
            TaskCreateRequest(name="Test Task", max_retries=11)


class TestTaskUpdateRequest:
    def test_valid_task_update_request(self):
        request = TaskUpdateRequest(
            name="Updated Task",
            priority=TaskPriority.LOW,
            payload={"updated": "data"},
            max_retries=2,
        )

        assert request.name == "Updated Task"
        assert request.priority == TaskPriority.LOW
        assert request.payload == {"updated": "data"}
        assert request.max_retries == 2

    def test_task_update_request_all_none(self):
        request = TaskUpdateRequest()

        assert request.name is None
        assert request.priority is None
        assert request.payload is None
        assert request.scheduled_at is None
        assert request.max_retries is None


class TestTaskResponse:
    def test_task_response_creation(self):
        response = TaskResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="Test Task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            payload={"key": "value"},
            created_at=datetime.now(),
            scheduled_at=None,
            retry_count=0,
            max_retries=3,
        )

        assert response.id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.name == "Test Task"
        assert response.status == TaskStatus.PENDING
        assert response.priority == TaskPriority.MEDIUM
        assert response.payload == {"key": "value"}
        assert response.retry_count == 0
        assert response.max_retries == 3


class TestWorkerCreateRequest:
    def test_valid_worker_create_request(self):
        request = WorkerCreateRequest(
            name="Test Worker", capabilities=["general", "data-processing"]
        )

        assert request.name == "Test Worker"
        assert request.capabilities == ["general", "data-processing"]

    def test_worker_create_request_defaults(self):
        request = WorkerCreateRequest(name="Test Worker")

        assert request.name == "Test Worker"
        assert request.capabilities == []

    def test_worker_create_request_validation(self):
        # Test empty name
        with pytest.raises(ValidationError):
            WorkerCreateRequest(name="")


class TestWorkerUpdateRequest:
    def test_valid_worker_update_request(self):
        request = WorkerUpdateRequest(
            name="Updated Worker",
            capabilities=["updated", "capabilities"],
            status=WorkerStatus.MAINTENANCE,
        )

        assert request.name == "Updated Worker"
        assert request.capabilities == ["updated", "capabilities"]
        assert request.status == WorkerStatus.MAINTENANCE

    def test_worker_update_request_all_none(self):
        request = WorkerUpdateRequest()

        assert request.name is None
        assert request.capabilities is None
        assert request.status is None


class TestWorkerResponse:
    def test_worker_response_creation(self):
        response = WorkerResponse(
            id="123e4567-e89b-12d3-a456-426614174000",
            name="Test Worker",
            status=WorkerStatus.IDLE,
            capabilities=["general"],
            current_task_id=None,
            last_heartbeat=datetime.now(),
        )

        assert response.id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.name == "Test Worker"
        assert response.status == WorkerStatus.IDLE
        assert response.capabilities == ["general"]
        assert response.current_task_id is None


class TestTaskResultResponse:
    def test_task_result_response_creation(self):
        response = TaskResultResponse(
            task_id="123e4567-e89b-12d3-a456-426614174000",
            worker_id="123e4567-e89b-12d3-a456-426614174001",
            status=TaskStatus.COMPLETED,
            result_data={"result": "success"},
            error_message=None,
            execution_time_ms=1000,
            completed_at=datetime.now(),
        )

        assert response.task_id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.worker_id == "123e4567-e89b-12d3-a456-426614174001"
        assert response.status == TaskStatus.COMPLETED
        assert response.result_data == {"result": "success"}
        assert response.error_message is None
        assert response.execution_time_ms == 1000


class TestWorkerHeartbeatRequest:
    def test_worker_heartbeat_request(self):
        request = WorkerHeartbeatRequest(
            worker_id="123e4567-e89b-12d3-a456-426614174000",
            status=WorkerStatus.BUSY,
            current_task_id="123e4567-e89b-12d3-a456-426614174001",
        )

        assert request.worker_id == "123e4567-e89b-12d3-a456-426614174000"
        assert request.status == WorkerStatus.BUSY
        assert request.current_task_id == "123e4567-e89b-12d3-a456-426614174001"

    def test_worker_heartbeat_request_minimal(self):
        request = WorkerHeartbeatRequest(
            worker_id="123e4567-e89b-12d3-a456-426614174000"
        )

        assert request.worker_id == "123e4567-e89b-12d3-a456-426614174000"
        assert request.status is None
        assert request.current_task_id is None


class TestTaskAssignmentRequest:
    def test_task_assignment_request(self):
        request = TaskAssignmentRequest(
            worker_id="123e4567-e89b-12d3-a456-426614174000",
            task_id="123e4567-e89b-12d3-a456-426614174001",
        )

        assert request.worker_id == "123e4567-e89b-12d3-a456-426614174000"
        assert request.task_id == "123e4567-e89b-12d3-a456-426614174001"


class TestTaskCompletionRequest:
    def test_task_completion_request(self):
        request = TaskCompletionRequest(
            task_id="123e4567-e89b-12d3-a456-426614174000",
            worker_id="123e4567-e89b-12d3-a456-426614174001",
            result_data={"result": "success"},
            execution_time_ms=1000,
        )

        assert request.task_id == "123e4567-e89b-12d3-a456-426614174000"
        assert request.worker_id == "123e4567-e89b-12d3-a456-426614174001"
        assert request.result_data == {"result": "success"}
        assert request.execution_time_ms == 1000


class TestTaskFailureRequest:
    def test_task_failure_request(self):
        request = TaskFailureRequest(
            task_id="123e4567-e89b-12d3-a456-426614174000",
            worker_id="123e4567-e89b-12d3-a456-426614174001",
            error_message="Task failed",
            execution_time_ms=500,
        )

        assert request.task_id == "123e4567-e89b-12d3-a456-426614174000"
        assert request.worker_id == "123e4567-e89b-12d3-a456-426614174001"
        assert request.error_message == "Task failed"
        assert request.execution_time_ms == 500
