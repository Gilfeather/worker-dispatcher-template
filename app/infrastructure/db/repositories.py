from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from ...domain.entities import Task, TaskId, Worker, WorkerId, TaskResult
from ...domain.enums import TaskStatus, TaskPriority, WorkerStatus
from ...domain.services.repository_interfaces import TaskRepository, WorkerRepository, TaskResultRepository
from .models import TaskModel, WorkerModel, TaskResultModel
from ..exceptions import DatabaseConnectionException


class SQLAlchemyTaskRepository(TaskRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, task: Task) -> None:
        try:
            existing = await self.session.get(TaskModel, task.id.value)
            if existing:
                existing.name = task.name
                existing.status = task.status.value
                existing.priority = task.priority.value
                existing.payload = task.payload
                existing.scheduled_at = task.scheduled_at
                existing.retry_count = task.retry_count
                existing.max_retries = task.max_retries
            else:
                model = TaskModel(
                    id=task.id.value,
                    name=task.name,
                    status=task.status.value,
                    priority=task.priority.value,
                    payload=task.payload,
                    scheduled_at=task.scheduled_at,
                    retry_count=task.retry_count,
                    max_retries=task.max_retries
                )
                self.session.add(model)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise DatabaseConnectionException(f"Failed to save task: {str(e)}")
    
    async def get_by_id(self, task_id: TaskId) -> Optional[Task]:
        try:
            result = await self.session.get(TaskModel, task_id.value)
            return self._model_to_entity(result) if result else None
        except Exception as e:
            raise DatabaseConnectionException(f"Failed to get task by id: {str(e)}")
    
    async def get_pending_tasks(self) -> List[Task]:
        try:
            result = await self.session.execute(
                select(TaskModel).where(TaskModel.status == TaskStatus.PENDING.value)
            )
            return [self._model_to_entity(model) for model in result.scalars().all()]
        except Exception as e:
            raise DatabaseConnectionException(f"Failed to get pending tasks: {str(e)}")
    
    async def get_by_status(self, status: str) -> List[Task]:
        try:
            result = await self.session.execute(
                select(TaskModel).where(TaskModel.status == status)
            )
            return [self._model_to_entity(model) for model in result.scalars().all()]
        except Exception as e:
            raise DatabaseConnectionException(f"Failed to get tasks by status: {str(e)}")
    
    async def delete(self, task_id: TaskId) -> None:
        try:
            await self.session.execute(
                delete(TaskModel).where(TaskModel.id == task_id.value)
            )
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise DatabaseConnectionException(f"Failed to delete task: {str(e)}")
    
    def _model_to_entity(self, model: TaskModel) -> Task:
        return Task(
            id=TaskId(model.id),
            name=model.name,
            status=TaskStatus(model.status),
            priority=TaskPriority(model.priority),
            payload=model.payload or {},
            created_at=model.created_at,
            scheduled_at=model.scheduled_at,
            retry_count=model.retry_count,
            max_retries=model.max_retries
        )


class SQLAlchemyWorkerRepository(WorkerRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, worker: Worker) -> None:
        try:
            existing = await self.session.get(WorkerModel, worker.id.value)
            if existing:
                existing.name = worker.name
                existing.status = worker.status.value
                existing.capabilities = worker.capabilities
                existing.current_task_id = worker.current_task.value if worker.current_task else None
                existing.last_heartbeat = worker.last_heartbeat
            else:
                model = WorkerModel(
                    id=worker.id.value,
                    name=worker.name,
                    status=worker.status.value,
                    capabilities=worker.capabilities,
                    current_task_id=worker.current_task.value if worker.current_task else None,
                    last_heartbeat=worker.last_heartbeat
                )
                self.session.add(model)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise DatabaseConnectionException(f"Failed to save worker: {str(e)}")
    
    async def get_by_id(self, worker_id: WorkerId) -> Optional[Worker]:
        try:
            result = await self.session.get(WorkerModel, worker_id.value)
            return self._model_to_entity(result) if result else None
        except Exception as e:
            raise DatabaseConnectionException(f"Failed to get worker by id: {str(e)}")
    
    async def get_all(self) -> List[Worker]:
        try:
            result = await self.session.execute(select(WorkerModel))
            return [self._model_to_entity(model) for model in result.scalars().all()]
        except Exception as e:
            raise DatabaseConnectionException(f"Failed to get all workers: {str(e)}")
    
    async def get_available(self) -> List[Worker]:
        try:
            result = await self.session.execute(
                select(WorkerModel).where(WorkerModel.status == WorkerStatus.IDLE.value)
            )
            return [self._model_to_entity(model) for model in result.scalars().all()]
        except Exception as e:
            raise DatabaseConnectionException(f"Failed to get available workers: {str(e)}")
    
    async def delete(self, worker_id: WorkerId) -> None:
        try:
            await self.session.execute(
                delete(WorkerModel).where(WorkerModel.id == worker_id.value)
            )
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise DatabaseConnectionException(f"Failed to delete worker: {str(e)}")
    
    def _model_to_entity(self, model: WorkerModel) -> Worker:
        return Worker(
            id=WorkerId(model.id),
            name=model.name,
            status=WorkerStatus(model.status),
            capabilities=model.capabilities or [],
            current_task=TaskId(model.current_task_id) if model.current_task_id else None,
            last_heartbeat=model.last_heartbeat
        )


class SQLAlchemyTaskResultRepository(TaskResultRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save(self, result: TaskResult) -> None:
        try:
            execution_time_ms = None
            if result.execution_time:
                execution_time_ms = int(result.execution_time.total_seconds() * 1000)
            
            model = TaskResultModel(
                task_id=result.task_id.value,
                worker_id=result.worker_id.value,
                status=result.status.value,
                result_data=result.result_data,
                error_message=result.error_message,
                execution_time_ms=execution_time_ms,
                completed_at=result.completed_at
            )
            self.session.add(model)
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise DatabaseConnectionException(f"Failed to save task result: {str(e)}")
    
    async def get_by_task_id(self, task_id: TaskId) -> Optional[TaskResult]:
        try:
            result = await self.session.execute(
                select(TaskResultModel).where(TaskResultModel.task_id == task_id.value)
            )
            model = result.scalars().first()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            raise DatabaseConnectionException(f"Failed to get task result by task id: {str(e)}")
    
    async def get_by_worker_id(self, worker_id: WorkerId) -> List[TaskResult]:
        try:
            result = await self.session.execute(
                select(TaskResultModel).where(TaskResultModel.worker_id == worker_id.value)
            )
            return [self._model_to_entity(model) for model in result.scalars().all()]
        except Exception as e:
            raise DatabaseConnectionException(f"Failed to get task results by worker id: {str(e)}")
    
    def _model_to_entity(self, model: TaskResultModel) -> TaskResult:
        from datetime import timedelta
        execution_time = None
        if model.execution_time_ms:
            execution_time = timedelta(milliseconds=model.execution_time_ms)
        
        return TaskResult(
            task_id=TaskId(model.task_id),
            worker_id=WorkerId(model.worker_id),
            status=TaskStatus(model.status),
            result_data=model.result_data,
            error_message=model.error_message,
            execution_time=execution_time,
            completed_at=model.completed_at
        )