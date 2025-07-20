from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import uuid

from ...domain.entities import Task, TaskId, Worker, WorkerId, TaskResult
from ...domain.enums import TaskStatus, TaskPriority, WorkerStatus
from ...domain.services.worker_dispatcher_impl import WorkerDispatcherImpl
from ...domain.services.worker_management_impl import WorkerManagementImpl
from ...infrastructure.db.repositories import SQLAlchemyTaskResultRepository
from ..interface import (
    get_dispatcher_service,
    get_worker_management_service,
    get_result_repository,
)
from .schemas import (
    WorkerCreateRequest,
    WorkerResponse,
    TaskCompletionRequest,
    TaskFailureRequest,
    WorkerHeartbeatRequest,
)


router = APIRouter()


@router.post("/register", response_model=WorkerResponse)
async def register_as_worker(
    worker_request: WorkerCreateRequest,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> WorkerResponse:
    """Register this instance as a worker"""
    worker = Worker(
        id=WorkerId(uuid.uuid4()),
        name=worker_request.name,
        capabilities=worker_request.capabilities,
        status=WorkerStatus.IDLE,
    )

    await worker_management.register_worker(worker)

    return WorkerResponse(
        id=str(worker.id),
        name=worker.name,
        status=worker.status,
        capabilities=worker.capabilities,
        current_task_id=str(worker.current_task) if worker.current_task else None,
        last_heartbeat=worker.last_heartbeat,
    )


@router.get("/next-task")
async def get_next_task(
    worker_id: str,
    capabilities: Optional[str] = None,
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> Dict[str, Any]:
    """Get the next available task for this worker"""
    # Get worker
    worker = await worker_management.get_worker_by_id(WorkerId(worker_id))
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    if not worker.is_available():
        raise HTTPException(status_code=400, detail="Worker is not available")

    # Update capabilities if provided
    if capabilities:
        worker.capabilities = capabilities.split(",")
        await worker_management.register_worker(worker)  # Update worker

    # Get next task
    task = await dispatcher.get_next_task(worker)

    if not task:
        return {"task": None, "message": "No tasks available"}

    # Assign task to worker
    await dispatcher.assign_task_to_worker(task.id, worker.id)

    return {
        "task": {
            "id": str(task.id),
            "name": task.name,
            "priority": task.priority.value,
            "payload": task.payload,
            "created_at": task.created_at.isoformat(),
            "scheduled_at": task.scheduled_at.isoformat()
            if task.scheduled_at
            else None,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
        },
        "message": "Task assigned successfully",
    }


@router.post("/complete-task")
async def complete_task(
    completion: TaskCompletionRequest,
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
    result_repo: SQLAlchemyTaskResultRepository = Depends(get_result_repository),
) -> Dict[str, str]:
    """Mark a task as completed by this worker"""
    try:
        # Complete the task
        await dispatcher.complete_task(
            TaskId(completion.task_id), WorkerId(completion.worker_id)
        )

        # If execution time provided, update the result
        if completion.execution_time_ms is not None:
            result = await result_repo.get_by_task_id(TaskId(completion.task_id))
            if result:
                result.execution_time = timedelta(
                    milliseconds=completion.execution_time_ms
                )
                if completion.result_data:
                    result.result_data = completion.result_data
                await result_repo.save(result)

        return {"message": "Task completed successfully"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fail-task")
async def fail_task(
    failure: TaskFailureRequest,
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
) -> Dict[str, str]:
    """Mark a task as failed by this worker"""
    try:
        await dispatcher.fail_task(
            TaskId(failure.task_id), WorkerId(failure.worker_id), failure.error_message
        )

        return {"message": "Task marked as failed"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/heartbeat")
async def send_heartbeat(
    heartbeat: WorkerHeartbeatRequest,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> Dict[str, str]:
    """Send heartbeat from this worker"""
    try:
        await worker_management.update_worker_heartbeat(WorkerId(heartbeat.worker_id))

        # Update status if provided
        if heartbeat.status:
            await worker_management.update_worker_status(
                WorkerId(heartbeat.worker_id), heartbeat.status.value
            )

        return {"message": "Heartbeat updated successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Heartbeat update failed: {str(e)}"
        )


@router.get("/status/{worker_id}")
async def get_worker_status(
    worker_id: str,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> Dict[str, Any]:
    """Get status of a specific worker"""
    worker = await worker_management.get_worker_by_id(WorkerId(worker_id))

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    return {
        "worker_id": str(worker.id),
        "name": worker.name,
        "status": worker.status.value,
        "capabilities": worker.capabilities,
        "current_task_id": str(worker.current_task) if worker.current_task else None,
        "last_heartbeat": worker.last_heartbeat.isoformat(),
        "is_healthy": worker.is_healthy(),
        "is_available": worker.is_available(),
    }


@router.post("/process-tasks")
async def start_task_processing(
    worker_id: str,
    background_tasks: BackgroundTasks,
    max_tasks: Optional[int] = 10,
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> Dict[str, Any]:
    """Start processing tasks continuously for this worker"""
    # Verify worker exists
    worker = await worker_management.get_worker_by_id(WorkerId(worker_id))
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Start background task processing
    background_tasks.add_task(
        process_tasks_continuously, worker_id, max_tasks, dispatcher, worker_management
    )

    return {
        "message": f"Started continuous task processing for worker {worker_id}",
        "max_tasks": max_tasks,
    }


@router.post("/stop-processing")
async def stop_task_processing(
    worker_id: str,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> Dict[str, str]:
    """Stop task processing for this worker"""
    # Set worker to maintenance mode to stop processing
    await worker_management.update_worker_status(
        WorkerId(worker_id), WorkerStatus.MAINTENANCE.value
    )

    return {"message": f"Stopped task processing for worker {worker_id}"}


@router.get("/my-tasks/{worker_id}")
async def get_worker_tasks(
    worker_id: str,
    limit: int = 10,
    result_repo: SQLAlchemyTaskResultRepository = Depends(get_result_repository),
) -> Dict[str, Any]:
    """Get tasks processed by this worker"""
    results = await result_repo.get_by_worker_id(WorkerId(worker_id))

    # Apply limit
    results = results[:limit] if isinstance(results, list) else []

    task_history = []
    for result in results:
        task_history.append(
            {
                "task_id": str(result.task_id),
                "status": result.status.value,
                "result_data": result.result_data,
                "error_message": result.error_message,
                "execution_time_ms": int(result.execution_time.total_seconds() * 1000)
                if result.execution_time
                else None,
                "completed_at": result.completed_at.isoformat(),
            }
        )

    return {
        "worker_id": worker_id,
        "task_history": task_history,
        "total_tasks": len(task_history),
    }


async def process_tasks_continuously(
    worker_id: str,
    max_tasks: int,
    dispatcher: WorkerDispatcherImpl,
    worker_management: WorkerManagementImpl,
):
    """Continuously process tasks for a worker"""
    processed_count = 0

    try:
        while processed_count < max_tasks:
            # Get worker status
            worker = await worker_management.get_worker_by_id(WorkerId(worker_id))
            if not worker or worker.status == WorkerStatus.MAINTENANCE:
                break  # Stop processing

            if not worker.is_available():
                await asyncio.sleep(5)  # Wait if busy
                continue

            # Get next task
            task = await dispatcher.get_next_task(worker)
            if not task:
                await asyncio.sleep(10)  # No tasks available, wait
                continue

            # Assign and process task
            await dispatcher.assign_task_to_worker(task.id, worker.id)

            # Simulate task processing
            success = await simulate_task_processing(task)

            if success:
                await dispatcher.complete_task(task.id, worker.id)
            else:
                await dispatcher.fail_task(task.id, worker.id, "Task processing failed")

            processed_count += 1

    except Exception as e:
        import logging

        logging.error(
            f"Error in continuous task processing for worker {worker_id}: {e}"
        )


async def simulate_task_processing(task: Task) -> bool:
    """Simulate task processing"""
    try:
        # Get processing time from payload or use default
        processing_time = task.payload.get("processing_time", 5)
        failure_rate = task.payload.get("failure_rate", 0.1)  # 10% failure rate

        # Simulate processing
        await asyncio.sleep(min(processing_time, 30))  # Cap at 30 seconds

        # Simulate occasional failures
        import random

        return random.random() > failure_rate

    except Exception:
        return False


@router.get("/capabilities")
async def get_available_capabilities(
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
) -> Dict[str, Any]:
    """Get all available capabilities from registered workers"""
    workers = await worker_management.get_worker_statistics()

    return {
        "available_capabilities": list(workers["capability_distribution"].keys()),
        "capability_counts": workers["capability_distribution"],
        "total_workers": workers["total_workers"],
    }
