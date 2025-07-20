"""
Example usage of the Worker Dispatcher API
Demonstrates how to use the /dispatch and /work endpoints in the same container
"""

import asyncio
import aiohttp
import json
from datetime import datetime


class WorkerDispatcherClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    # Dispatch endpoints
    async def dispatch_task(self, name: str, payload: dict, priority: str = "medium"):
        """Dispatch a new task"""
        data = {"name": name, "priority": priority, "payload": payload}

        async with self.session.post(
            f"{self.base_url}/dispatch/task", json=data
        ) as response:
            return await response.json()

    async def dispatch_bulk_tasks(self, tasks: list):
        """Dispatch multiple tasks"""
        async with self.session.post(
            f"{self.base_url}/dispatch/task/bulk", json=tasks
        ) as response:
            return await response.json()

    async def get_queue_status(self):
        """Get current queue status"""
        async with self.session.get(
            f"{self.base_url}/dispatch/queue/status"
        ) as response:
            return await response.json()

    async def get_available_workers(self):
        """Get available workers"""
        async with self.session.get(
            f"{self.base_url}/dispatch/available-workers"
        ) as response:
            return await response.json()

    # Work endpoints
    async def register_worker(self, name: str, capabilities: list):
        """Register as a worker"""
        data = {"name": name, "capabilities": capabilities}

        async with self.session.post(
            f"{self.base_url}/work/register", json=data
        ) as response:
            return await response.json()

    async def get_next_task(self, worker_id: str, capabilities: str = None):
        """Get next task for worker"""
        params = {}
        if capabilities:
            params["capabilities"] = capabilities

        async with self.session.get(
            f"{self.base_url}/work/next-task", params={"worker_id": worker_id, **params}
        ) as response:
            return await response.json()

    async def complete_task(
        self, task_id: str, worker_id: str, result_data: dict = None
    ):
        """Mark task as completed"""
        data = {
            "task_id": task_id,
            "worker_id": worker_id,
            "result_data": result_data or {"status": "success"},
        }

        async with self.session.post(
            f"{self.base_url}/work/complete-task", json=data
        ) as response:
            return await response.json()

    async def fail_task(self, task_id: str, worker_id: str, error_message: str):
        """Mark task as failed"""
        data = {
            "task_id": task_id,
            "worker_id": worker_id,
            "error_message": error_message,
        }

        async with self.session.post(
            f"{self.base_url}/work/fail-task", json=data
        ) as response:
            return await response.json()

    async def send_heartbeat(self, worker_id: str, status: str = None):
        """Send worker heartbeat"""
        data = {"worker_id": worker_id}
        if status:
            data["status"] = status

        async with self.session.post(
            f"{self.base_url}/work/heartbeat", json=data
        ) as response:
            return await response.json()

    async def start_task_processing(self, worker_id: str, max_tasks: int = 10):
        """Start continuous task processing"""
        async with self.session.post(
            f"{self.base_url}/work/process-tasks",
            params={"worker_id": worker_id, "max_tasks": max_tasks},
        ) as response:
            return await response.json()


async def demo_dispatch_workflow():
    """Demonstrate dispatcher workflow"""
    print("=== Dispatcher Workflow Demo ===")

    async with WorkerDispatcherClient() as client:
        # 1. Dispatch some tasks
        print("\n1. Dispatching tasks...")

        tasks = [
            {
                "name": "Process data file 1",
                "priority": "high",
                "payload": {
                    "file_path": "/data/file1.csv",
                    "processing_time": 3,
                    "required_capabilities": ["data-processing"],
                },
            },
            {
                "name": "Generate report",
                "priority": "medium",
                "payload": {
                    "report_type": "monthly",
                    "processing_time": 5,
                    "required_capabilities": ["reporting"],
                },
            },
            {
                "name": "Send notifications",
                "priority": "low",
                "payload": {
                    "recipients": ["user1@example.com", "user2@example.com"],
                    "processing_time": 2,
                },
            },
        ]

        # Dispatch individual task
        result = await client.dispatch_task(
            name="Test Task",
            payload={"test": True, "processing_time": 1},
            priority="high",
        )
        print(f"Dispatched task: {result}")

        # Dispatch bulk tasks
        bulk_result = await client.dispatch_bulk_tasks(tasks)
        print(f"Dispatched {len(bulk_result)} tasks in bulk")

        # 2. Check queue status
        print("\n2. Checking queue status...")
        queue_status = await client.get_queue_status()
        print(f"Queue status: {queue_status}")

        # 3. Check available workers
        print("\n3. Checking available workers...")
        workers = await client.get_available_workers()
        print(f"Available workers: {workers}")


async def demo_worker_workflow():
    """Demonstrate worker workflow"""
    print("\n=== Worker Workflow Demo ===")

    async with WorkerDispatcherClient() as client:
        # 1. Register as a worker
        print("\n1. Registering as worker...")
        worker_result = await client.register_worker(
            name="Demo Worker", capabilities=["general", "data-processing", "reporting"]
        )
        worker_id = worker_result["id"]
        print(f"Registered worker: {worker_result}")

        # 2. Process some tasks manually
        print("\n2. Processing tasks manually...")
        for i in range(3):
            # Send heartbeat
            await client.send_heartbeat(worker_id, "idle")

            # Get next task
            task_result = await client.get_next_task(worker_id)

            if task_result["task"]:
                task = task_result["task"]
                task_id = task["id"]
                print(f"Got task: {task['name']} (ID: {task_id})")

                # Simulate processing
                processing_time = task["payload"].get("processing_time", 1)
                print(f"Processing for {processing_time} seconds...")
                await asyncio.sleep(processing_time)

                # Complete task
                try:
                    complete_result = await client.complete_task(
                        task_id,
                        worker_id,
                        {"processed_at": datetime.now().isoformat(), "success": True},
                    )
                    print(f"Completed task: {complete_result}")
                except Exception as e:
                    # If completion fails, mark as failed
                    fail_result = await client.fail_task(task_id, worker_id, str(e))
                    print(f"Failed task: {fail_result}")
            else:
                print("No tasks available")
                break

        # 3. Start continuous processing
        print("\n3. Starting continuous task processing...")
        processing_result = await client.start_task_processing(worker_id, max_tasks=5)
        print(f"Started processing: {processing_result}")

        # Wait a bit for processing to happen
        await asyncio.sleep(10)

        print("\nDemo completed!")


async def demo_full_workflow():
    """Demonstrate complete workflow combining dispatch and work"""
    print("=== Full Workflow Demo ===")
    print(
        "This demo shows how the same container can act as both dispatcher and worker"
    )

    # Run dispatcher workflow first
    await demo_dispatch_workflow()

    # Then run worker workflow
    await demo_worker_workflow()


async def health_check():
    """Check if the service is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"Service is healthy: {result}")
                    return True
                else:
                    print(f"Service health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"Could not connect to service: {e}")
        return False


if __name__ == "__main__":

    async def main():
        print("Worker Dispatcher Example Usage")
        print("==============================")

        # Check if service is running
        if not await health_check():
            print("Please start the service first with: docker-compose up -d")
            return

        # Run the demo
        await demo_full_workflow()

    asyncio.run(main())
