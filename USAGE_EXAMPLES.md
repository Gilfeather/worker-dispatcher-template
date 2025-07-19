# Usage Examples

This document provides practical examples of how to use the Worker Dispatcher with the new `/dispatch` and `/work` endpoints in the same container.

## 🏗️ Architecture Overview

The new design allows a single container to act as both:
- **Dispatcher**: Distributes tasks via `/dispatch` endpoints
- **Worker**: Processes tasks via `/work` endpoints

## 🚀 Quick Examples

### 1. Dispatch a Task

```bash
curl -X POST "http://localhost:8000/dispatch/task" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Process data file",
    "priority": "high",
    "payload": {
      "file_path": "/data/sample.csv",
      "processing_time": 5,
      "required_capabilities": ["data-processing"]
    }
  }'
```

### 2. Register as a Worker

```bash
curl -X POST "http://localhost:8000/work/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Processor Worker",
    "capabilities": ["data-processing", "file-processing", "general"]
  }'
```

### 3. Get Next Task to Process

```bash
curl "http://localhost:8000/work/next-task?worker_id=YOUR_WORKER_ID"
```

### 4. Complete a Task

```bash
curl -X POST "http://localhost:8000/work/complete-task" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK_ID",
    "worker_id": "WORKER_ID",
    "result_data": {
      "processed_records": 1000,
      "processing_time_ms": 5000,
      "status": "success"
    }
  }'
```

## 📱 Python Client Example

```python
import asyncio
import aiohttp

class WorkerDispatcherClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    async def dispatch_and_process_workflow(self):
        async with aiohttp.ClientSession() as session:
            # 1. Register as a worker
            worker_data = {
                "name": "Example Worker",
                "capabilities": ["general", "data-processing"]
            }
            
            async with session.post(f"{self.base_url}/work/register", json=worker_data) as resp:
                worker = await resp.json()
                worker_id = worker["id"]
                print(f"Registered worker: {worker_id}")
            
            # 2. Dispatch a task
            task_data = {
                "name": "Example Task",
                "priority": "medium",
                "payload": {"data": "example", "processing_time": 2}
            }
            
            async with session.post(f"{self.base_url}/dispatch/task", json=task_data) as resp:
                task = await resp.json()
                print(f"Dispatched task: {task['id']}")
            
            # 3. Process the task
            params = {"worker_id": worker_id}
            async with session.get(f"{self.base_url}/work/next-task", params=params) as resp:
                result = await resp.json()
                
                if result["task"]:
                    task_info = result["task"]
                    print(f"Got task to process: {task_info['name']}")
                    
                    # Simulate processing
                    await asyncio.sleep(task_info["payload"].get("processing_time", 1))
                    
                    # Complete the task
                    complete_data = {
                        "task_id": task_info["id"],
                        "worker_id": worker_id,
                        "result_data": {"status": "completed", "result": "success"}
                    }
                    
                    async with session.post(f"{self.base_url}/work/complete-task", json=complete_data) as resp:
                        complete_result = await resp.json()
                        print(f"Task completed: {complete_result}")

# Run the example
asyncio.run(WorkerDispatcherClient().dispatch_and_process_workflow())
```

## 🔄 Continuous Processing

### Start Continuous Task Processing

```bash
curl -X POST "http://localhost:8000/work/process-tasks?worker_id=YOUR_WORKER_ID&max_tasks=10"
```

This will start background processing for up to 10 tasks.

### Stop Processing

```bash
curl -X POST "http://localhost:8000/work/stop-processing" \
  -H "Content-Type: application/json" \
  -d '{"worker_id": "YOUR_WORKER_ID"}'
```

## 📊 Monitoring and Status

### Check Queue Status

```bash
curl "http://localhost:8000/dispatch/queue/status"
```

### Get Available Workers

```bash
curl "http://localhost:8000/dispatch/available-workers"
```

### Get Worker Status

```bash
curl "http://localhost:8000/work/status/YOUR_WORKER_ID"
```

### Send Heartbeat

```bash
curl -X POST "http://localhost:8000/work/heartbeat" \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "YOUR_WORKER_ID",
    "status": "idle"
  }'
```

## 🎯 Use Cases

### 1. Microservice Architecture

Each microservice can register as a worker with specific capabilities:

```python
# Service A: Data Processing
worker_data = {
    "name": "Data Processing Service",
    "capabilities": ["data-processing", "etl", "analytics"]
}

# Service B: File Processing  
worker_data = {
    "name": "File Processing Service",
    "capabilities": ["file-processing", "image-resize", "pdf-generation"]
}

# Service C: Notification Service
worker_data = {
    "name": "Notification Service", 
    "capabilities": ["email", "sms", "push-notifications"]
}
```

### 2. Load Balancing

Dispatch tasks and let the system automatically assign them to available workers:

```python
# Dispatch multiple tasks
tasks = [
    {"name": "Process order #1001", "payload": {"order_id": 1001}},
    {"name": "Process order #1002", "payload": {"order_id": 1002}},
    {"name": "Process order #1003", "payload": {"order_id": 1003}},
]

# Bulk dispatch
async with session.post(f"{base_url}/dispatch/task/bulk", json=tasks) as resp:
    results = await resp.json()
```

### 3. Scheduled Processing

Dispatch tasks with specific scheduling:

```python
from datetime import datetime, timedelta

# Schedule task for later
future_time = datetime.now() + timedelta(hours=1)
task_data = {
    "name": "Scheduled Report Generation",
    "scheduled_at": future_time.isoformat(),
    "payload": {"report_type": "daily"}
}
```

### 4. Capability-Based Routing

Tasks are automatically routed to workers with matching capabilities:

```python
# Task requiring specific capabilities
task_data = {
    "name": "Process ML Model",
    "payload": {
        "model_path": "/models/classifier.pkl",
        "required_capabilities": ["machine-learning", "gpu"]
    }
}
```

## 🛠️ Advanced Configuration

### Worker Registration with Custom Capabilities

```bash
curl -X POST "http://localhost:8000/work/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Specialized Worker",
    "capabilities": [
      "machine-learning",
      "computer-vision", 
      "gpu-processing",
      "python-3.9",
      "tensorflow",
      "high-memory"
    ]
  }'
```

### Task with Complex Payload

```bash
curl -X POST "http://localhost:8000/dispatch/task" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Complex Data Pipeline",
    "priority": "high",
    "max_retries": 5,
    "payload": {
      "input_files": ["/data/file1.csv", "/data/file2.csv"],
      "output_path": "/results/processed/",
      "processing_options": {
        "remove_duplicates": true,
        "normalize_data": true,
        "apply_filters": ["age > 18", "status = active"]
      },
      "required_capabilities": ["data-processing", "pandas", "high-memory"],
      "processing_time": 30,
      "failure_rate": 0.05
    }
  }'
```

## 🔍 Troubleshooting

### Check System Health

```bash
curl "http://localhost:8000/health"
curl "http://localhost:8000/api/v1/monitoring/health"
```

### Get Comprehensive Stats

```bash
curl "http://localhost:8000/dispatch/stats"
curl "http://localhost:8000/api/v1/monitoring/dashboard"
```

### View Worker Task History

```bash
curl "http://localhost:8000/work/my-tasks/YOUR_WORKER_ID?limit=20"
```

## 🚀 Production Considerations

### 1. Multiple Container Instances

Scale horizontally by running multiple containers:

```bash
# Scale with Docker Compose
docker-compose up -d --scale app=3

# Each instance can act as both dispatcher and worker
```

### 2. Load Balancer Configuration

Configure your load balancer to route:
- POST `/dispatch/*` → Any instance (stateless)
- GET/POST `/work/*` → Sticky sessions or any instance

### 3. Database Connection Pooling

Ensure proper database connection pooling for multiple instances:

```python
# In production configuration
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db?pool_size=20&max_overflow=30"
```

This design provides flexibility to run everything in a single container while maintaining the separation of concerns between dispatching and working responsibilities.