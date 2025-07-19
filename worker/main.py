import asyncio
import logging
import os
import signal
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
import json

from app.domain.entities import Worker, WorkerId, TaskId
from app.domain.enums import WorkerStatus, TaskStatus


class WorkerClient:
    def __init__(self, api_base_url: str, worker_name: str, capabilities: list):
        self.api_base_url = api_base_url
        self.worker_name = worker_name
        self.capabilities = capabilities
        self.worker_id: Optional[str] = None
        self.running = False
        self.current_task: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def start(self):
        """Start the worker"""
        self.session = aiohttp.ClientSession()
        self.running = True
        
        # Register worker
        await self.register_worker()
        
        # Start heartbeat task
        asyncio.create_task(self.heartbeat_loop())
        
        # Start main worker loop
        await self.worker_loop()
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        
        if self.worker_id:
            await self.unregister_worker()
        
        if self.session:
            await self.session.close()
    
    async def register_worker(self):
        """Register this worker with the dispatcher"""
        try:
            payload = {
                "name": self.worker_name,
                "capabilities": self.capabilities
            }
            
            async with self.session.post(
                f"{self.api_base_url}/api/v1/workers/",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.worker_id = data["id"]
                    logging.info(f"Worker registered with ID: {self.worker_id}")
                else:
                    logging.error(f"Failed to register worker: {response.status}")
                    
        except Exception as e:
            logging.error(f"Error registering worker: {e}")
    
    async def unregister_worker(self):
        """Unregister this worker"""
        try:
            async with self.session.delete(
                f"{self.api_base_url}/api/v1/workers/{self.worker_id}"
            ) as response:
                if response.status == 200:
                    logging.info("Worker unregistered successfully")
                else:
                    logging.error(f"Failed to unregister worker: {response.status}")
                    
        except Exception as e:
            logging.error(f"Error unregistering worker: {e}")
    
    async def heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(15)  # Send heartbeat every 15 seconds
            except Exception as e:
                logging.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)
    
    async def send_heartbeat(self):
        """Send heartbeat to dispatcher"""
        if not self.worker_id:
            return
            
        try:
            payload = {
                "worker_id": self.worker_id,
                "status": WorkerStatus.BUSY.value if self.current_task else WorkerStatus.IDLE.value,
                "current_task_id": self.current_task
            }
            
            async with self.session.post(
                f"{self.api_base_url}/api/v1/workers/{self.worker_id}/heartbeat",
                json=payload
            ) as response:
                if response.status != 200:
                    logging.warning(f"Heartbeat failed: {response.status}")
                    
        except Exception as e:
            logging.error(f"Error sending heartbeat: {e}")
    
    async def worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                if not self.current_task:
                    # Try to get a task
                    task = await self.get_next_task()
                    if task:
                        self.current_task = task["id"]
                        logging.info(f"Received task: {task['id']} - {task['name']}")
                        
                        # Process the task
                        await self.process_task(task)
                        
                        self.current_task = None
                    else:
                        # No tasks available, wait a bit
                        await asyncio.sleep(5)
                else:
                    # Already processing a task, wait
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logging.error(f"Error in worker loop: {e}")
                await asyncio.sleep(5)
    
    async def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next available task"""
        try:
            async with self.session.get(
                f"{self.api_base_url}/api/v1/tasks/",
                params={"status": "pending", "limit": 1}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        return data[0]
                        
        except Exception as e:
            logging.error(f"Error getting next task: {e}")
            
        return None
    
    async def process_task(self, task: Dict[str, Any]):
        """Process a task"""
        task_id = task["id"]
        task_name = task["name"]
        payload = task["payload"]
        
        try:
            logging.info(f"Processing task {task_id}: {task_name}")
            
            # Simulate task processing
            processing_time = payload.get("processing_time", 5)
            await asyncio.sleep(processing_time)
            
            # Mark task as completed
            await self.complete_task(task_id, {"result": "success", "processed_at": datetime.now().isoformat()})
            
            logging.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logging.error(f"Error processing task {task_id}: {e}")
            await self.fail_task(task_id, str(e))
    
    async def complete_task(self, task_id: str, result_data: Dict[str, Any]):
        """Mark a task as completed"""
        try:
            payload = {
                "task_id": task_id,
                "worker_id": self.worker_id,
                "result_data": result_data
            }
            
            async with self.session.post(
                f"{self.api_base_url}/api/v1/tasks/{task_id}/complete",
                json=payload
            ) as response:
                if response.status != 200:
                    logging.error(f"Failed to complete task: {response.status}")
                    
        except Exception as e:
            logging.error(f"Error completing task: {e}")
    
    async def fail_task(self, task_id: str, error_message: str):
        """Mark a task as failed"""
        try:
            payload = {
                "task_id": task_id,
                "worker_id": self.worker_id,
                "error_message": error_message
            }
            
            async with self.session.post(
                f"{self.api_base_url}/api/v1/tasks/{task_id}/fail",
                json=payload
            ) as response:
                if response.status != 200:
                    logging.error(f"Failed to fail task: {response.status}")
                    
        except Exception as e:
            logging.error(f"Error failing task: {e}")


async def main():
    """Main entry point"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Get configuration from environment
    api_base_url = os.getenv("API_BASE_URL", "http://app:8000")
    worker_name = os.getenv("WORKER_NAME", "worker-1")
    capabilities = os.getenv("WORKER_CAPABILITIES", "general").split(",")
    
    # Create worker client
    worker_client = WorkerClient(api_base_url, worker_name, capabilities)
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logging.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(worker_client.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start worker
    try:
        await worker_client.start()
    except KeyboardInterrupt:
        logging.info("Worker interrupted by user")
    except Exception as e:
        logging.error(f"Worker error: {e}")
    finally:
        await worker_client.stop()


if __name__ == "__main__":
    asyncio.run(main())