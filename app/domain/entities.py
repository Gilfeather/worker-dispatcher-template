from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .enums import TaskStatus, TaskPriority, WorkerStatus


class TaskId(BaseModel):
    value: UUID = Field(default_factory=uuid4)
    
    def __str__(self) -> str:
        return str(self.value)
    
    class Config:
        arbitrary_types_allowed = True


class WorkerId(BaseModel):
    value: UUID = Field(default_factory=uuid4)
    
    def __str__(self) -> str:
        return str(self.value)
    
    class Config:
        arbitrary_types_allowed = True


class Task(BaseModel):
    id: TaskId = Field(default_factory=TaskId)
    name: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    @validator('name')
    def validate_name(cls, v):
        if v and len(v.strip()) == 0:
            raise ValueError('Task name cannot be empty')
        return v
    
    @validator('max_retries')
    def validate_max_retries(cls, v):
        if v < 0:
            raise ValueError('Max retries cannot be negative')
        return v
    
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries
    
    def increment_retry(self) -> None:
        self.retry_count += 1
    
    def is_completed(self) -> bool:
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    def should_execute(self) -> bool:
        if self.scheduled_at is None:
            return True
        return datetime.now() >= self.scheduled_at
    
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True


class Worker(BaseModel):
    id: WorkerId = Field(default_factory=WorkerId)
    name: str = ""
    status: WorkerStatus = WorkerStatus.IDLE
    capabilities: List[str] = Field(default_factory=list)
    current_task: Optional[TaskId] = None
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    
    @validator('name')
    def validate_name(cls, v):
        if v and len(v.strip()) == 0:
            raise ValueError('Worker name cannot be empty')
        return v
    
    def is_available(self) -> bool:
        return self.status == WorkerStatus.IDLE
    
    def assign_task(self, task_id: TaskId) -> None:
        self.current_task = task_id
        self.status = WorkerStatus.BUSY
    
    def complete_task(self) -> None:
        self.current_task = None
        self.status = WorkerStatus.IDLE
    
    def update_heartbeat(self) -> None:
        self.last_heartbeat = datetime.now()
    
    def is_healthy(self, timeout_seconds: int = 30) -> bool:
        return (datetime.now() - self.last_heartbeat).total_seconds() < timeout_seconds
    
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True


class TaskResult(BaseModel):
    task_id: TaskId
    worker_id: WorkerId
    status: TaskStatus
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[timedelta] = None
    completed_at: datetime = Field(default_factory=datetime.now)
    
    def is_success(self) -> bool:
        return self.status == TaskStatus.COMPLETED
    
    def is_failure(self) -> bool:
        return self.status == TaskStatus.FAILED
    
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True