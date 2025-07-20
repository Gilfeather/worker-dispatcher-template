from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from ...domain.enums import TaskStatus, TaskPriority, WorkerStatus


class TaskCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    priority: TaskPriority = TaskPriority.MEDIUM
    payload: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    max_retries: Optional[int] = Field(default=3, ge=0, le=10)


class TaskUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    priority: Optional[TaskPriority] = None
    payload: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)


class TaskResponse(BaseModel):
    id: str
    name: str
    status: TaskStatus
    priority: TaskPriority
    payload: Dict[str, Any]
    created_at: datetime
    scheduled_at: Optional[datetime]
    retry_count: int
    max_retries: int

    class Config:
        from_attributes = True


class WorkerCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    capabilities: List[str] = Field(default_factory=list)


class WorkerUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    capabilities: Optional[List[str]] = None
    status: Optional[WorkerStatus] = None


class WorkerResponse(BaseModel):
    id: str
    name: str
    status: WorkerStatus
    capabilities: List[str]
    current_task_id: Optional[str]
    last_heartbeat: datetime

    class Config:
        from_attributes = True


class TaskResultResponse(BaseModel):
    task_id: str
    worker_id: str
    status: TaskStatus
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    completed_at: datetime

    class Config:
        from_attributes = True


class WorkerHeartbeatRequest(BaseModel):
    worker_id: str
    status: Optional[WorkerStatus] = None
    current_task_id: Optional[str] = None


class TaskAssignmentRequest(BaseModel):
    worker_id: str
    task_id: str


class TaskCompletionRequest(BaseModel):
    task_id: str
    worker_id: str
    result_data: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None


class TaskFailureRequest(BaseModel):
    task_id: str
    worker_id: str
    error_message: str
    execution_time_ms: Optional[int] = None


class QueueStatisticsResponse(BaseModel):
    queue_size: int
    priority_distribution: Dict[str, int]
    timestamp: str


class WorkerStatisticsResponse(BaseModel):
    total_workers: int
    status_distribution: Dict[str, int]
    capability_distribution: Dict[str, int]
    healthy_workers: int
    unhealthy_workers: int


class SystemHealthResponse(BaseModel):
    status: str
    database_connected: bool
    active_workers: int
    pending_tasks: int
    failed_tasks: int
    timestamp: datetime
