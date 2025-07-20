from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from ...domain.entities import Task, TaskId, TaskResult
from ...domain.enums import TaskStatus, TaskPriority
from ...domain.services.worker_dispatcher_impl import WorkerDispatcherImpl
from ...infrastructure.db.repositories import (
    SQLAlchemyTaskRepository,
    SQLAlchemyTaskResultRepository,
)
from ..interface import (
    get_dispatcher_service,
    get_task_repository,
    get_result_repository,
)
from .schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
    TaskResultResponse,
)


router = APIRouter()


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_request: TaskCreateRequest,
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
) -> TaskResponse:
    """Create a new task"""
    task = Task(
        id=TaskId(uuid4()),
        name=task_request.name,
        priority=task_request.priority,
        payload=task_request.payload,
        scheduled_at=task_request.scheduled_at,
        max_retries=task_request.max_retries or 3,
    )

    await dispatcher.enqueue_task(task)

    return TaskResponse(
        id=str(task.id),
        name=task.name,
        status=task.status,
        priority=task.priority,
        payload=task.payload,
        created_at=task.created_at,
        scheduled_at=task.scheduled_at,
        retry_count=task.retry_count,
        max_retries=task.max_retries,
    )


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    task_repo: SQLAlchemyTaskRepository = Depends(get_task_repository),
) -> List[TaskResponse]:
    """Get tasks with optional filtering"""
    if status:
        tasks = await task_repo.get_by_status(status.value)
    else:
        tasks = await task_repo.get_pending_tasks()

    # Apply priority filter if specified
    if priority:
        tasks = [task for task in tasks if task.priority == priority]

    # Apply pagination
    tasks = tasks[offset : offset + limit]

    return [
        TaskResponse(
            id=str(task.id),
            name=task.name,
            status=task.status,
            priority=task.priority,
            payload=task.payload,
            created_at=task.created_at,
            scheduled_at=task.scheduled_at,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
        )
        for task in tasks
    ]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str, dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service)
) -> TaskResponse:
    """Get a specific task by ID"""
    task = await dispatcher.get_task_by_id(TaskId(task_id))

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        id=str(task.id),
        name=task.name,
        status=task.status,
        priority=task.priority,
        payload=task.payload,
        created_at=task.created_at,
        scheduled_at=task.scheduled_at,
        retry_count=task.retry_count,
        max_retries=task.max_retries,
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdateRequest,
    task_repo: SQLAlchemyTaskRepository = Depends(get_task_repository),
) -> TaskResponse:
    """Update a task"""
    task = await task_repo.get_by_id(TaskId(task_id))

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update fields if provided
    if task_update.name is not None:
        task.name = task_update.name
    if task_update.priority is not None:
        task.priority = task_update.priority
    if task_update.payload is not None:
        task.payload = task_update.payload
    if task_update.scheduled_at is not None:
        task.scheduled_at = task_update.scheduled_at
    if task_update.max_retries is not None:
        task.max_retries = task_update.max_retries

    await task_repo.save(task)

    return TaskResponse(
        id=str(task.id),
        name=task.name,
        status=task.status,
        priority=task.priority,
        payload=task.payload,
        created_at=task.created_at,
        scheduled_at=task.scheduled_at,
        retry_count=task.retry_count,
        max_retries=task.max_retries,
    )


@router.delete("/{task_id}")
async def delete_task(
    task_id: str, task_repo: SQLAlchemyTaskRepository = Depends(get_task_repository)
) -> Dict[str, str]:
    """Delete a task"""
    task = await task_repo.get_by_id(TaskId(task_id))

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await task_repo.delete(TaskId(task_id))

    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str, dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service)
) -> Dict[str, str]:
    """Manually retry a failed task"""
    task = await dispatcher.get_task_by_id(TaskId(task_id))

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status not in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Task cannot be retried")

    if not task.can_retry():
        raise HTTPException(status_code=400, detail="Task has exceeded maximum retries")

    # Reset task for retry
    task.status = TaskStatus.PENDING
    task.increment_retry()

    await dispatcher.enqueue_task(task)

    return {"message": "Task queued for retry"}


@router.get("/{task_id}/result", response_model=TaskResultResponse)
async def get_task_result(
    task_id: str,
    result_repo: SQLAlchemyTaskResultRepository = Depends(get_result_repository),
) -> TaskResultResponse:
    """Get the result of a task"""
    result = await result_repo.get_by_task_id(TaskId(task_id))

    if not result:
        raise HTTPException(status_code=404, detail="Task result not found")

    return TaskResultResponse(
        task_id=str(result.task_id),
        worker_id=str(result.worker_id),
        status=result.status,
        result_data=result.result_data,
        error_message=result.error_message,
        execution_time_ms=int(result.execution_time.total_seconds() * 1000)
        if result.execution_time
        else None,
        completed_at=result.completed_at,
    )


@router.get("/{task_id}/history", response_model=List[TaskResultResponse])
async def get_task_history(
    task_id: str,
    result_repo: SQLAlchemyTaskResultRepository = Depends(get_result_repository),
) -> List[TaskResultResponse]:
    """Get the execution history of a task"""
    results = await result_repo.get_by_task_id(TaskId(task_id))

    if not results:
        return []

    return [
        TaskResultResponse(
            task_id=str(result.task_id),
            worker_id=str(result.worker_id),
            status=result.status,
            result_data=result.result_data,
            error_message=result.error_message,
            execution_time_ms=int(result.execution_time.total_seconds() * 1000)
            if result.execution_time
            else None,
            completed_at=result.completed_at,
        )
        for result in results
        if isinstance(results, list)
    ]


@router.post("/bulk", response_model=List[TaskResponse])
async def create_bulk_tasks(
    tasks: List[TaskCreateRequest],
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
) -> List[TaskResponse]:
    """Create multiple tasks in bulk"""
    created_tasks = []

    for task_request in tasks:
        task = Task(
            id=TaskId(uuid4()),
            name=task_request.name,
            priority=task_request.priority,
            payload=task_request.payload,
            scheduled_at=task_request.scheduled_at,
            max_retries=task_request.max_retries or 3,
        )

        await dispatcher.enqueue_task(task)

        created_tasks.append(
            TaskResponse(
                id=str(task.id),
                name=task.name,
                status=task.status,
                priority=task.priority,
                payload=task.payload,
                created_at=task.created_at,
                scheduled_at=task.scheduled_at,
                retry_count=task.retry_count,
                max_retries=task.max_retries,
            )
        )

    return created_tasks
