from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime

from ...domain.services.worker_dispatcher_impl import WorkerDispatcherImpl
from ...domain.services.worker_management_impl import WorkerManagementImpl
from ...infrastructure.db.repositories import SQLAlchemyTaskRepository, SQLAlchemyWorkerRepository
from ..interface import (
    get_dispatcher_service, 
    get_worker_management_service, 
    get_task_repository, 
    get_worker_repository
)
from .schemas import QueueStatisticsResponse, WorkerStatisticsResponse, SystemHealthResponse


router = APIRouter()


@router.get("/health", response_model=SystemHealthResponse)
async def system_health(
    task_repo: SQLAlchemyTaskRepository = Depends(get_task_repository),
    worker_repo: SQLAlchemyWorkerRepository = Depends(get_worker_repository)
) -> SystemHealthResponse:
    """Get system health status"""
    try:
        # Check database connectivity
        database_connected = True
        try:
            await task_repo.get_pending_tasks()
        except Exception:
            database_connected = False
        
        # Get worker count
        workers = await worker_repo.get_all()
        active_workers = len([w for w in workers if w.is_healthy()])
        
        # Get task counts
        pending_tasks = await task_repo.get_by_status("pending")
        failed_tasks = await task_repo.get_by_status("failed")
        
        status = "healthy" if database_connected and active_workers > 0 else "unhealthy"
        
        return SystemHealthResponse(
            status=status,
            database_connected=database_connected,
            active_workers=active_workers,
            pending_tasks=len(pending_tasks),
            failed_tasks=len(failed_tasks),
            timestamp=datetime.now()
        )
    except Exception as e:
        return SystemHealthResponse(
            status="error",
            database_connected=False,
            active_workers=0,
            pending_tasks=0,
            failed_tasks=0,
            timestamp=datetime.now()
        )


@router.get("/queue/statistics", response_model=QueueStatisticsResponse)
async def get_queue_statistics(
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service)
) -> QueueStatisticsResponse:
    """Get queue statistics"""
    stats = await dispatcher.get_queue_statistics()
    
    return QueueStatisticsResponse(
        queue_size=stats["queue_size"],
        priority_distribution=stats["priority_distribution"],
        timestamp=stats["timestamp"]
    )


@router.get("/workers/statistics", response_model=WorkerStatisticsResponse)
async def get_worker_statistics(
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> WorkerStatisticsResponse:
    """Get worker statistics"""
    stats = await worker_management.get_worker_statistics()
    
    return WorkerStatisticsResponse(
        total_workers=stats["total_workers"],
        status_distribution=stats["status_distribution"],
        capability_distribution=stats["capability_distribution"],
        healthy_workers=stats["healthy_workers"],
        unhealthy_workers=stats["unhealthy_workers"]
    )


@router.get("/metrics")
async def get_metrics(
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
    task_repo: SQLAlchemyTaskRepository = Depends(get_task_repository)
) -> Dict[str, Any]:
    """Get comprehensive system metrics"""
    
    # Get queue statistics
    queue_stats = await dispatcher.get_queue_statistics()
    
    # Get worker statistics
    worker_stats = await worker_management.get_worker_statistics()
    
    # Get task statistics by status
    task_stats = {}
    for status in ["pending", "in_progress", "completed", "failed", "cancelled"]:
        tasks = await task_repo.get_by_status(status)
        task_stats[status] = len(tasks)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "queue": queue_stats,
        "workers": worker_stats,
        "tasks": task_stats,
        "system": {
            "uptime": "calculated from startup",
            "version": "1.0.0"
        }
    }


@router.post("/cleanup/tasks")
async def cleanup_old_tasks(
    max_age_hours: int = 24,
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service)
) -> Dict[str, Any]:
    """Clean up old completed/failed tasks"""
    try:
        cleanup_count = await dispatcher.cleanup_expired_tasks(max_age_hours)
        
        return {
            "message": f"Cleaned up {cleanup_count} old tasks",
            "cleaned_count": cleanup_count,
            "max_age_hours": max_age_hours,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.post("/cleanup/workers")
async def cleanup_offline_workers(
    max_offline_hours: int = 24,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> Dict[str, Any]:
    """Clean up workers that have been offline for too long"""
    try:
        cleaned_ids = await worker_management.cleanup_offline_workers(max_offline_hours)
        
        return {
            "message": f"Cleaned up {len(cleaned_ids)} offline workers",
            "cleaned_worker_ids": [str(worker_id) for worker_id in cleaned_ids],
            "max_offline_hours": max_offline_hours,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.post("/maintenance/mark_unhealthy_offline")
async def mark_unhealthy_workers_offline(
    timeout_seconds: int = 30,
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> Dict[str, Any]:
    """Mark unhealthy workers as offline"""
    try:
        offline_ids = await worker_management.mark_unhealthy_workers_offline(timeout_seconds)
        
        return {
            "message": f"Marked {len(offline_ids)} workers as offline",
            "offline_worker_ids": [str(worker_id) for worker_id in offline_ids],
            "timeout_seconds": timeout_seconds,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Maintenance operation failed: {str(e)}")


@router.post("/maintenance/reassign_failed_tasks")
async def reassign_failed_worker_tasks(
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service)
) -> Dict[str, Any]:
    """Reassign tasks from failed workers"""
    try:
        failed_worker_ids = await worker_management.reassign_tasks_from_failed_workers()
        
        return {
            "message": f"Reassigned tasks from {len(failed_worker_ids)} failed workers",
            "failed_worker_ids": [str(worker_id) for worker_id in failed_worker_ids],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reassignment failed: {str(e)}")


@router.get("/dashboard")
async def get_dashboard_data(
    dispatcher: WorkerDispatcherImpl = Depends(get_dispatcher_service),
    worker_management: WorkerManagementImpl = Depends(get_worker_management_service),
    task_repo: SQLAlchemyTaskRepository = Depends(get_task_repository)
) -> Dict[str, Any]:
    """Get dashboard data for monitoring UI"""
    
    # Get current statistics
    queue_stats = await dispatcher.get_queue_statistics()
    worker_stats = await worker_management.get_worker_statistics()
    
    # Get recent task counts
    recent_tasks = {
        "pending": len(await task_repo.get_by_status("pending")),
        "in_progress": len(await task_repo.get_by_status("in_progress")),
        "completed": len(await task_repo.get_by_status("completed")),
        "failed": len(await task_repo.get_by_status("failed"))
    }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_workers": worker_stats["total_workers"],
            "healthy_workers": worker_stats["healthy_workers"],
            "queue_size": queue_stats["queue_size"],
            "total_tasks": sum(recent_tasks.values())
        },
        "queue": queue_stats,
        "workers": worker_stats,
        "tasks": recent_tasks
    }