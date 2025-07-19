from datetime import datetime, timedelta
from typing import List, Optional

from ..entities import Worker, WorkerId
from ..enums import WorkerStatus
from .worker_management import WorkerManagementService
from .repository_interfaces import WorkerRepository


class WorkerManagementImpl(WorkerManagementService):
    def __init__(self, worker_repository: WorkerRepository):
        self.worker_repository = worker_repository
    
    async def register_worker(self, worker: Worker) -> None:
        """Register a new worker"""
        worker.update_heartbeat()
        await self.worker_repository.save(worker)
    
    async def unregister_worker(self, worker_id: WorkerId) -> None:
        """Unregister a worker"""
        await self.worker_repository.delete(worker_id)
    
    async def update_worker_heartbeat(self, worker_id: WorkerId) -> None:
        """Update worker heartbeat timestamp"""
        worker = await self.worker_repository.get_by_id(worker_id)
        if worker:
            worker.update_heartbeat()
            await self.worker_repository.save(worker)
    
    async def get_available_workers(self) -> List[Worker]:
        """Get all available workers"""
        return await self.worker_repository.get_available()
    
    async def get_worker_by_id(self, worker_id: WorkerId) -> Optional[Worker]:
        """Get a specific worker by ID"""
        return await self.worker_repository.get_by_id(worker_id)
    
    async def get_worker_by_capabilities(self, capabilities: List[str]) -> List[Worker]:
        """Get workers that have the specified capabilities"""
        all_workers = await self.worker_repository.get_all()
        matching_workers = []
        
        for worker in all_workers:
            if worker.is_available() and all(cap in worker.capabilities for cap in capabilities):
                matching_workers.append(worker)
        
        return matching_workers
    
    async def update_worker_status(self, worker_id: WorkerId, status: str) -> None:
        """Update worker status"""
        worker = await self.worker_repository.get_by_id(worker_id)
        if worker:
            worker.status = WorkerStatus(status)
            await self.worker_repository.save(worker)
    
    async def check_worker_health(self, timeout_seconds: int = 30) -> List[Worker]:
        """Check health of all workers and return unhealthy ones"""
        all_workers = await self.worker_repository.get_all()
        unhealthy_workers = []
        
        for worker in all_workers:
            if not worker.is_healthy(timeout_seconds):
                unhealthy_workers.append(worker)
        
        return unhealthy_workers
    
    async def mark_unhealthy_workers_offline(self, timeout_seconds: int = 30) -> List[WorkerId]:
        """Mark unhealthy workers as offline"""
        unhealthy_workers = await self.check_worker_health(timeout_seconds)
        offline_worker_ids = []
        
        for worker in unhealthy_workers:
            if worker.status != WorkerStatus.OFFLINE:
                worker.status = WorkerStatus.OFFLINE
                await self.worker_repository.save(worker)
                offline_worker_ids.append(worker.id)
        
        return offline_worker_ids
    
    async def get_worker_statistics(self) -> dict:
        """Get statistics about workers"""
        all_workers = await self.worker_repository.get_all()
        
        stats = {
            "total_workers": len(all_workers),
            "status_distribution": {},
            "capability_distribution": {},
            "healthy_workers": 0,
            "unhealthy_workers": 0
        }
        
        capability_counts = {}
        
        for worker in all_workers:
            # Count status distribution
            status = worker.status.value
            stats["status_distribution"][status] = stats["status_distribution"].get(status, 0) + 1
            
            # Count health
            if worker.is_healthy():
                stats["healthy_workers"] += 1
            else:
                stats["unhealthy_workers"] += 1
            
            # Count capabilities
            for capability in worker.capabilities:
                capability_counts[capability] = capability_counts.get(capability, 0) + 1
        
        stats["capability_distribution"] = capability_counts
        
        return stats
    
    async def cleanup_offline_workers(self, max_offline_hours: int = 24) -> List[WorkerId]:
        """Clean up workers that have been offline for too long"""
        cutoff_time = datetime.now() - timedelta(hours=max_offline_hours)
        all_workers = await self.worker_repository.get_all()
        
        cleaned_up_ids = []
        
        for worker in all_workers:
            if (worker.status == WorkerStatus.OFFLINE and 
                worker.last_heartbeat < cutoff_time):
                await self.worker_repository.delete(worker.id)
                cleaned_up_ids.append(worker.id)
        
        return cleaned_up_ids
    
    async def reassign_tasks_from_failed_workers(self) -> List[WorkerId]:
        """Reassign tasks from workers that have failed"""
        all_workers = await self.worker_repository.get_all()
        failed_workers = []
        
        for worker in all_workers:
            if (worker.status == WorkerStatus.OFFLINE and 
                worker.current_task is not None and
                not worker.is_healthy()):
                
                # Mark worker as having no current task
                worker.current_task = None
                worker.status = WorkerStatus.OFFLINE
                await self.worker_repository.save(worker)
                
                failed_workers.append(worker.id)
        
        return failed_workers