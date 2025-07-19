import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from app.domain.entities import Task, Worker, TaskResult, TaskId, WorkerId
from app.domain.enums import TaskStatus, TaskPriority, WorkerStatus
from app.domain.services.repository_interfaces import TaskRepository, WorkerRepository, TaskResultRepository
from app.domain.services.worker_dispatcher_impl import WorkerDispatcherImpl
from app.domain.services.worker_management_impl import WorkerManagementImpl


@pytest.fixture
def sample_task():
    """Create a sample task for testing"""
    return Task(
        name="Test Task",
        priority=TaskPriority.MEDIUM,
        payload={"test": "data"}
    )


@pytest.fixture
def sample_worker():
    """Create a sample worker for testing"""
    return Worker(
        name="Test Worker",
        capabilities=["general", "data-processing"]
    )


@pytest.fixture
def sample_task_result(sample_task, sample_worker):
    """Create a sample task result for testing"""
    return TaskResult(
        task_id=sample_task.id,
        worker_id=sample_worker.id,
        status=TaskStatus.COMPLETED,
        result_data={"result": "success"}
    )


@pytest.fixture
def mock_task_repository():
    """Create a mock task repository"""
    mock_repo = AsyncMock(spec=TaskRepository)
    mock_repo.save = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.get_pending_tasks = AsyncMock(return_value=[])
    mock_repo.get_by_status = AsyncMock(return_value=[])
    mock_repo.delete = AsyncMock()
    return mock_repo


@pytest.fixture
def mock_worker_repository():
    """Create a mock worker repository"""
    mock_repo = AsyncMock(spec=WorkerRepository)
    mock_repo.save = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.get_all = AsyncMock(return_value=[])
    mock_repo.get_available = AsyncMock(return_value=[])
    mock_repo.delete = AsyncMock()
    return mock_repo


@pytest.fixture
def mock_result_repository():
    """Create a mock result repository"""
    mock_repo = AsyncMock(spec=TaskResultRepository)
    mock_repo.save = AsyncMock()
    mock_repo.get_by_task_id = AsyncMock()
    mock_repo.get_by_worker_id = AsyncMock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_worker_management(mock_worker_repository):
    """Create a mock worker management service"""
    return WorkerManagementImpl(mock_worker_repository)


@pytest.fixture
def mock_dispatcher(mock_task_repository, mock_worker_repository, mock_result_repository, mock_worker_management):
    """Create a mock dispatcher service"""
    return WorkerDispatcherImpl(
        mock_task_repository,
        mock_worker_repository,
        mock_result_repository,
        mock_worker_management
    )


@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def anyio_backend():
    """Use asyncio backend for anyio tests"""
    return "asyncio"


class MockAsyncSession:
    """Mock async database session"""
    def __init__(self):
        self.add = MagicMock()
        self.delete = MagicMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.execute = AsyncMock()
        self.get = AsyncMock()
        self.scalars = MagicMock()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return MockAsyncSession()


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing external API calls"""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"success": True})
    mock_response.read = AsyncMock(return_value=b"test data")
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.put = AsyncMock(return_value=mock_response)
    mock_client.delete = AsyncMock(return_value=mock_response)
    return mock_client