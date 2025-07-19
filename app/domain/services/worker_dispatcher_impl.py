import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict
import heapq

from ..entities import Task, TaskId, Worker, WorkerId, TaskResult
from ..enums import TaskStatus, TaskPriority, WorkerStatus
from .task_dispatcher import TaskDispatcherService
from .worker_management import WorkerManagementService
from .repository_interfaces import TaskRepository, WorkerRepository, TaskResultRepository


class WorkerDispatcherImpl(TaskDispatcherService):
    def __init__(
        self,
        task_repository: TaskRepository,
        worker_repository: WorkerRepository,
        result_repository: TaskResultRepository,
        worker_management: WorkerManagementService
    ):
        self.task_repository = task_repository
        self.worker_repository = worker_repository
        self.result_repository = result_repository
        self.worker_management = worker_management
        self.task_queue: List[Task] = []
        self.priority_weights = {
            TaskPriority.CRITICAL: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1
        }
        self._queue_lock = asyncio.Lock()
    
    async def enqueue_task(self, task: Task) -> None:
        """Enqueue a task with priority ordering"""
        async with self._queue_lock:
            await self.task_repository.save(task)
            
            # Insert task into priority queue
            priority_score = self.priority_weights[task.priority]
            heapq.heappush(self.task_queue, (-priority_score, task.created_at, task))
    
    async def get_next_task(self, worker: Worker) -> Optional[Task]:
        """Get the next available task for a worker based on capabilities"""
        async with self._queue_lock:
            if not self.task_queue:
                await self._reload_pending_tasks()
            
            # Find the highest priority task that matches worker capabilities
            available_tasks = []
            while self.task_queue:
                priority_score, created_at, task = heapq.heappop(self.task_queue)
                
                # Check if task should be executed now
                if not task.should_execute():
                    # Put back in queue for later
                    heapq.heappush(self.task_queue, (priority_score, created_at, task))
                    continue
                
                # Check if worker can handle this task
                if self._can_worker_handle_task(worker, task):
                    return task
                
                # Store task for later re-queuing
                available_tasks.append((priority_score, created_at, task))
            
            # Re-queue tasks that couldn't be handled
            for task_tuple in available_tasks:
                heapq.heappush(self.task_queue, task_tuple)
            
            return None
    
    async def assign_task_to_worker(self, task_id: TaskId, worker_id: WorkerId) -> None:
        """Assign a task to a specific worker"""
        task = await self.task_repository.get_by_id(task_id)
        worker = await self.worker_repository.get_by_id(worker_id)
        
        if not task or not worker:
            raise ValueError("Task or worker not found")
        
        if not worker.is_available():
            raise ValueError("Worker is not available")
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        await self.task_repository.save(task)
        
        # Update worker status
        worker.assign_task(task_id)
        await self.worker_repository.save(worker)
    
    async def complete_task(self, task_id: TaskId, worker_id: WorkerId) -> None:
        """Mark a task as completed"""
        task = await self.task_repository.get_by_id(task_id)
        worker = await self.worker_repository.get_by_id(worker_id)
        
        if not task or not worker:
            raise ValueError("Task or worker not found")
        
        # Update task status
        task.status = TaskStatus.COMPLETED
        await self.task_repository.save(task)
        
        # Update worker status
        worker.complete_task()
        await self.worker_repository.save(worker)
        
        # Store result
        result = TaskResult(
            task_id=task_id,
            worker_id=worker_id,
            status=TaskStatus.COMPLETED,
            completed_at=datetime.now()
        )
        await self.result_repository.save(result)
    
    async def fail_task(self, task_id: TaskId, worker_id: WorkerId, error_message: str) -> None:
        """Mark a task as failed and handle retry logic"""
        task = await self.task_repository.get_by_id(task_id)
        worker = await self.worker_repository.get_by_id(worker_id)
        
        if not task or not worker:
            raise ValueError("Task or worker not found")
        
        # Store failed result
        result = TaskResult(
            task_id=task_id,
            worker_id=worker_id,
            status=TaskStatus.FAILED,
            error_message=error_message,
            completed_at=datetime.now()
        )
        await self.result_repository.save(result)
        
        # Handle retry logic
        if task.can_retry():
            task.increment_retry()
            task.status = TaskStatus.RETRY
            # Add exponential backoff
            backoff_seconds = 2 ** task.retry_count
            task.scheduled_at = datetime.now() + timedelta(seconds=backoff_seconds)
            await self.task_repository.save(task)
            
            # Re-enqueue for retry
            await self.enqueue_task(task)
        else:
            # Mark as permanently failed
            task.status = TaskStatus.FAILED
            await self.task_repository.save(task)
        
        # Update worker status
        worker.complete_task()
        await self.worker_repository.save(worker)
    
    async def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        return await self.task_repository.get_by_status(TaskStatus.PENDING.value)
    
    async def get_task_by_id(self, task_id: TaskId) -> Optional[Task]:
        """Get a specific task by ID"""
        return await self.task_repository.get_by_id(task_id)
    
    async def _reload_pending_tasks(self) -> None:
        """Reload pending tasks from the database"""
        pending_tasks = await self.task_repository.get_pending_tasks()
        for task in pending_tasks:
            priority_score = self.priority_weights[task.priority]
            heapq.heappush(self.task_queue, (-priority_score, task.created_at, task))
    
    def _can_worker_handle_task(self, worker: Worker, task: Task) -> bool:
        """Check if a worker can handle a specific task based on capabilities"""
        if not worker.is_available():
            return False
        
        # If task requires specific capabilities, check if worker has them
        required_capabilities = task.payload.get("required_capabilities", [])
        if required_capabilities:
            return all(cap in worker.capabilities for cap in required_capabilities)
        
        return True
    
    async def get_queue_statistics(self) -> Dict[str, Any]:
        """Get statistics about the task queue"""
        async with self._queue_lock:
            queue_size = len(self.task_queue)
            priority_counts = defaultdict(int)
            
            for _, _, task in self.task_queue:
                priority_counts[task.priority.value] += 1
            
            return {
                "queue_size": queue_size,
                "priority_distribution": dict(priority_counts),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup_expired_tasks(self, max_age_hours: int = 24) -> int:
        """Clean up old completed/failed tasks"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Get old completed/failed tasks
        completed_tasks = await self.task_repository.get_by_status(TaskStatus.COMPLETED.value)
        failed_tasks = await self.task_repository.get_by_status(TaskStatus.FAILED.value)
        
        cleanup_count = 0
        for task in completed_tasks + failed_tasks:
            if task.created_at < cutoff_time:
                await self.task_repository.delete(task.id)
                cleanup_count += 1
        
        return cleanup_count