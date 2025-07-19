from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities import Worker, WorkerId


class WorkerManagementService(ABC):
    
    @abstractmethod
    async def register_worker(self, worker: Worker) -> None:
        pass
    
    @abstractmethod
    async def unregister_worker(self, worker_id: WorkerId) -> None:
        pass
    
    @abstractmethod
    async def update_worker_heartbeat(self, worker_id: WorkerId) -> None:
        pass
    
    @abstractmethod
    async def get_available_workers(self) -> List[Worker]:
        pass
    
    @abstractmethod
    async def get_worker_by_id(self, worker_id: WorkerId) -> Optional[Worker]:
        pass
    
    @abstractmethod
    async def get_worker_by_capabilities(self, capabilities: List[str]) -> List[Worker]:
        pass
    
    @abstractmethod
    async def update_worker_status(self, worker_id: WorkerId, status: str) -> None:
        pass