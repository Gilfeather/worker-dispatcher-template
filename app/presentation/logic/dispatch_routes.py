from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import uuid4

from ...domain.entities import Task, TaskId, Worker, WorkerId
from ...domain.enums import TaskStatus, TaskPriority, WorkerStatus
from ...domain.services.worker_dispatcher_impl import WorkerDispatcherImpl
from ...domain.services.worker_management_impl import WorkerManagementImpl
from ..interface import get_dispatcher_service, get_worker_management_service
from .schemas import TaskCreateRequest, TaskResponse, TaskAssignmentRequest


router = APIRouter()


@router.post("/task", response_model=TaskResponse)
async def dispatch_task(
    task_request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> TaskResponse:
    """Dispatch a new task to available workers"""
    # Create task
    task = Task(
        id=TaskId(uuid4()),
        name=task_request.name,
        priority=task_request.priority,
        payload=task_request.payload,
        scheduled_at=task_request.scheduled_at,
        max_retries=task_request.max_retries or 3,
    )

    # Enqueue task
    await dispatcher.enqueue_task(task)

    # Try to assign to available worker immediately
    background_tasks.add_task(try_assign_task, task.id, dispatcher, worker_management)

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


@router.post("/task/bulk", response_model=List[TaskResponse])
async def dispatch_bulk_tasks(
    tasks: List[TaskCreateRequest],
    background_tasks: BackgroundTasks,
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> List[TaskResponse]:
    """Dispatch multiple tasks in bulk"""
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

        # Try to assign to available worker
        background_tasks.add_task(
            try_assign_task, task.id, dispatcher, worker_management
        )

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


@router.post("/assign")
async def assign_task_to_worker(
    assignment: TaskAssignmentRequest,
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
) -> Dict[str, str]:
    """Manually assign a task to a specific worker"""
    try:
        await dispatcher.assign_task_to_worker(
            TaskId(assignment.task_id), WorkerId(assignment.worker_id)
        )
        return {"message": "Task assigned successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/queue/status")
async def get_queue_status(
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
) -> Dict[str, Any]:
    """Get current queue status"""
    stats = await dispatcher.get_queue_statistics()
    return {"queue_statistics": stats, "message": "Queue status retrieved successfully"}


@router.get("/available-workers")
async def get_available_workers(
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> Dict[str, Any]:
    """Get list of available workers"""
    available_workers = await worker_management.get_available_workers()

    return {
        "available_workers": [
            {
                "id": str(worker.id),
                "name": worker.name,
                "capabilities": worker.capabilities,
                "status": worker.status.value,
            }
            for worker in available_workers
        ],
        "count": len(available_workers),
    }


@router.post("/schedule")
async def schedule_task_processing(
    background_tasks: BackgroundTasks,
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> Dict[str, str]:
    """Trigger task processing for pending tasks"""
    background_tasks.add_task(process_pending_tasks, dispatcher, worker_management)
    return {"message": "Task processing scheduled"}


async def try_assign_task(
    task_id: TaskId,
    dispatcher: WorkerDispatcherImpl,
    worker_management: WorkerManagementImpl,
):
    """Try to assign a task to an available worker"""
    try:
        # Get available workers
        available_workers = await worker_management.get_available_workers()

        if not available_workers:
            return  # No workers available

        # Get the task
        task = await dispatcher.get_task_by_id(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return  # Task not found or not pending

        # Find a suitable worker
        suitable_worker = None
        required_capabilities = task.payload.get("required_capabilities", [])

        for worker in available_workers:
            if not required_capabilities or all(
                cap in worker.capabilities for cap in required_capabilities
            ):
                suitable_worker = worker
                break

        if suitable_worker:
            # Assign task to worker
            await dispatcher.assign_task_to_worker(task_id, suitable_worker.id)

    except Exception as e:
        # Log error but don't fail the request
        import logging

        logging.error(f"Error assigning task {task_id}: {e}")


async def process_pending_tasks(
    dispatcher: WorkerDispatcherImpl, worker_management: WorkerManagementImpl
):
    """Process all pending tasks by assigning them to available workers"""
    try:
        # Get pending tasks
        pending_tasks = await dispatcher.get_pending_tasks()

        for task in pending_tasks:
            if task.should_execute():
                await try_assign_task(task.id, dispatcher, worker_management)

    except Exception as e:
        import logging

        logging.error(f"Error processing pending tasks: {e}")


@router.get("/stats")
async def get_dispatch_statistics(
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> Dict[str, Any]:
    """Get comprehensive dispatch statistics"""
    queue_stats = await dispatcher.get_queue_statistics()
    worker_stats = await worker_management.get_worker_statistics()

    return {
        "queue": queue_stats,
        "workers": worker_stats,
        "dispatch_info": {
            "total_pending_tasks": queue_stats["queue_size"],
            "available_workers": worker_stats["status_distribution"].get("idle", 0),
            "busy_workers": worker_stats["status_distribution"].get("busy", 0),
        },
    }
