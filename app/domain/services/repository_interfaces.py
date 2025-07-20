from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities import Task, TaskId, TaskResult, Worker, WorkerId


class TaskRepository(ABC):
    @abstractmethod
    async def save(self, task: Task) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, task_id: TaskId) -> Optional[Task]:
        pass

    @abstractmethod
    async def get_pending_tasks(self) -> List[Task]:
        pass

    @abstractmethod
    async def get_by_status(self, status: str) -> List[Task]:
        pass

    @abstractmethod
    async def delete(self, task_id: TaskId) -> None:
        pass


class WorkerRepository(ABC):
    @abstractmethod
    async def save(self, worker: Worker) -> None:
        pass

    @abstractmethod
    async def get_by_id(self, worker_id: WorkerId) -> Optional[Worker]:
        pass

    @abstractmethod
    async def get_all(self) -> List[Worker]:
        pass

    @abstractmethod
    async def get_available(self) -> List[Worker]:
        pass

    @abstractmethod
    async def delete(self, worker_id: WorkerId) -> None:
        pass


class TaskResultRepository(ABC):
    @abstractmethod
    async def save(self, result: TaskResult) -> None:
        pass

    @abstractmethod
    async def get_by_task_id(self, task_id: TaskId) -> Optional[TaskResult]:
        pass

    @abstractmethod
    async def get_by_worker_id(self, worker_id: WorkerId) -> List[TaskResult]:
        pass
