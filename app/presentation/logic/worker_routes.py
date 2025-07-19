from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from ...domain.entities import Worker, WorkerId, TaskId
from ...domain.enums import WorkerStatus
from ...domain.services.worker_management_impl import WorkerManagementImpl
from ...infrastructure.db.repositories import SQLAlchemyWorkerRepository, SQLAlchemyTaskResultRepository
from ..interface import get_worker_management_service, get_worker_repository, get_result_repository
from .schemas import (
    WorkerCreateRequest, 
    WorkerResponse, 
    WorkerUpdateRequest, 
    WorkerHeartbeatRequest,
    TaskResultResponse
)


router = APIRouter()


@router.post("/", response_model=WorkerResponse)
async def register_worker(
    worker_request: WorkerCreateRequest,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> WorkerResponse:
    """Register a new worker"""
    worker = Worker(
        id=WorkerId(uuid4()),
        name=worker_request.name,
        capabilities=worker_request.capabilities,
        status=WorkerStatus.IDLE
    )
    
    await worker_management.register_worker(worker)
    
    return WorkerResponse(
        id=str(worker.id),
        name=worker.name,
        status=worker.status,
        capabilities=worker.capabilities,
        current_task_id=str(worker.current_task) if worker.current_task else None,
        last_heartbeat=worker.last_heartbeat
    )


@router.get("/", response_model=List[WorkerResponse])
async def get_workers(
    status: Optional[WorkerStatus] = Query(None),
    capability: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    worker_repo: SQLAlchemyWorkerRepository = Depends(get_worker_repository)
) -> List[WorkerResponse]:
    """Get workers with optional filtering"""
    if status and status == WorkerStatus.IDLE:
        workers = await worker_repo.get_available()
    else:
        workers = await worker_repo.get_all()
    
    # Apply status filter if specified
    if status and status != WorkerStatus.IDLE:
        workers = [worker for worker in workers if worker.status == status]
    
    # Apply capability filter if specified
    if capability:
        workers = [worker for worker in workers if capability in worker.capabilities]
    
    # Apply pagination
    workers = workers[offset:offset + limit]
    
    return [
        WorkerResponse(
            id=str(worker.id),
            name=worker.name,
            status=worker.status,
            capabilities=worker.capabilities,
            current_task_id=str(worker.current_task) if worker.current_task else None,
            last_heartbeat=worker.last_heartbeat
        )
        for worker in workers
    ]


@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(
    worker_id: str,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> WorkerResponse:
    """Get a specific worker by ID"""
    worker = await worker_management.get_worker_by_id(WorkerId(worker_id))
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    return WorkerResponse(
        id=str(worker.id),
        name=worker.name,
        status=worker.status,
        capabilities=worker.capabilities,
        current_task_id=str(worker.current_task) if worker.current_task else None,
        last_heartbeat=worker.last_heartbeat
    )


@router.put("/{worker_id}", response_model=WorkerResponse)
async def update_worker(
    worker_id: str,
    worker_update: WorkerUpdateRequest,
    worker_repo: SQLAlchemyWorkerRepository = Depends(get_worker_repository)
) -> WorkerResponse:
    """Update a worker"""
    worker = await worker_repo.get_by_id(WorkerId(worker_id))
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    # Update fields if provided
    if worker_update.name is not None:
        worker.name = worker_update.name
    if worker_update.capabilities is not None:
        worker.capabilities = worker_update.capabilities
    if worker_update.status is not None:
        worker.status = worker_update.status
    
    await worker_repo.save(worker)
    
    return WorkerResponse(
        id=str(worker.id),
        name=worker.name,
        status=worker.status,
        capabilities=worker.capabilities,
        current_task_id=str(worker.current_task) if worker.current_task else None,
        last_heartbeat=worker.last_heartbeat
    )


@router.delete("/{worker_id}")
async def unregister_worker(
    worker_id: str,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> Dict[str, str]:
    """Unregister a worker"""
    worker = await worker_management.get_worker_by_id(WorkerId(worker_id))
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    await worker_management.unregister_worker(WorkerId(worker_id))
    
    return {"message": "Worker unregistered successfully"}


@router.post("/{worker_id}/heartbeat")
async def worker_heartbeat(
    worker_id: str,
    heartbeat_request: WorkerHeartbeatRequest,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> Dict[str, str]:
    """Update worker heartbeat"""
    worker = await worker_management.get_worker_by_id(WorkerId(worker_id))
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    await worker_management.update_worker_heartbeat(WorkerId(worker_id))
    
    # Update status if provided
    if heartbeat_request.status:
        await worker_management.update_worker_status(WorkerId(worker_id), heartbeat_request.status.value)
    
    return {"message": "Heartbeat updated successfully"}


@router.get("/{worker_id}/tasks/history", response_model=List[TaskResultResponse])
async def get_worker_task_history(
    worker_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    result_repo: SQLAlchemyTaskResultRepository = Depends(get_result_repository)
) -> List[TaskResultResponse]:
    """Get the task execution history for a worker"""
    results = await result_repo.get_by_worker_id(WorkerId(worker_id))
    
    # Apply pagination
    results = results[offset:offset + limit]
    
    return [
        TaskResultResponse(
            task_id=str(result.task_id),
            worker_id=str(result.worker_id),
            status=result.status,
            result_data=result.result_data,
            error_message=result.error_message,
            execution_time_ms=int(result.execution_time.total_seconds() * 1000) if result.execution_time else None,
            completed_at=result.completed_at
        )
        for result in results
    ]


@router.get("/capabilities/{capability}", response_model=List[WorkerResponse])
async def get_workers_by_capability(
    capability: str,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> List[WorkerResponse]:
    """Get workers that have a specific capability"""
    workers = await worker_management.get_worker_by_capabilities([capability])
    
    return [
        WorkerResponse(
            id=str(worker.id),
            name=worker.name,
            status=worker.status,
            capabilities=worker.capabilities,
            current_task_id=str(worker.current_task) if worker.current_task else None,
            last_heartbeat=worker.last_heartbeat
        )
        for worker in workers
    ]


@router.post("/{worker_id}/maintenance")
async def set_worker_maintenance(
    worker_id: str,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> Dict[str, str]:
    """Set worker to maintenance mode"""
    worker = await worker_management.get_worker_by_id(WorkerId(worker_id))
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    await worker_management.update_worker_status(WorkerId(worker_id), WorkerStatus.MAINTENANCE.value)
    
    return {"message": "Worker set to maintenance mode"}


@router.post("/{worker_id}/activate")
async def activate_worker(
    worker_id: str,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> Dict[str, str]:
    """Activate worker from maintenance mode"""
    worker = await worker_management.get_worker_by_id(WorkerId(worker_id))
    
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    
    await worker_management.update_worker_status(WorkerId(worker_id), WorkerStatus.IDLE.value)
    
    return {"message": "Worker activated successfully"}


@router.get("/health/check")
async def check_worker_health(
    timeout_seconds: int = Query(30, ge=1, le=300),
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> Dict[str, Any]:
    """Check health of all workers"""
    unhealthy_workers = await worker_management.check_worker_health(timeout_seconds)
    
    return {
        "unhealthy_workers": [
            {
                "id": str(worker.id),
                "name": worker.name,
                "last_heartbeat": worker.last_heartbeat,
                "status": worker.status.value
            }
            for worker in unhealthy_workers
        ],
        "unhealthy_count": len(unhealthy_workers),
        "check_timestamp": datetime.now()
    }