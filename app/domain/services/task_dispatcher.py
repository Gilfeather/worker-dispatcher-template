from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities import Task, TaskId, Worker, WorkerId


class TaskDispatcherService(ABC):
    
    @abstractmethod
    async def enqueue_task(self, task: Task) -> None:
        pass
    
    @abstractmethod
    async def get_next_task(self, worker: Worker) -> Optional[Task]:
        pass
    
    @abstractmethod
    async def assign_task_to_worker(self, task_id: TaskId, worker_id: WorkerId) -> None:
        pass
    
    @abstractmethod
    async def complete_task(self, task_id: TaskId, worker_id: WorkerId) -> None:
        pass
    
    @abstractmethod
    async def fail_task(self, task_id: TaskId, worker_id: WorkerId, error_message: str) -> None:
        pass
    
    @abstractmethod
    async def get_pending_tasks(self) -> List[Task]:
        pass
    
    @abstractmethod
    async def get_task_by_id(self, task_id: TaskId) -> Optional[Task]:
        pass