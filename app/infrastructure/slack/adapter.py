from typing import Optional, Dict, Any, List
import aiohttp
import asyncio
from datetime import datetime

from ..exceptions import SlackServiceException


class SlackAdapter:
    def __init__(self, bot_token: str, webhook_url: Optional[str] = None):
        self.bot_token = bot_token
        self.webhook_url = webhook_url
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
    
    async def send_message(self, channel: str, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "channel": channel,
                    "text": text
                }
                if blocks:
                    payload["blocks"] = blocks
                
                async with session.post(
                    f"{self.base_url}/chat.postMessage",
                    headers=self.headers,
                    json=payload
                ) as response:
                    result = await response.json()
                    if not result.get("ok"):
                        raise SlackServiceException(f"Failed to send message: {result.get('error', 'Unknown error')}")
                    return result
        except aiohttp.ClientError as e:
            raise SlackServiceException(f"HTTP error sending message: {str(e)}")
    
    async def send_webhook_message(self, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> None:
        if not self.webhook_url:
            raise SlackServiceException("Webhook URL not configured")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"text": text}
                if blocks:
                    payload["blocks"] = blocks
                
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status != 200:
                        raise SlackServiceException(f"Webhook failed with status {response.status}")
        except aiohttp.ClientError as e:
            raise SlackServiceException(f"HTTP error sending webhook: {str(e)}")
    
    async def send_task_notification(self, task_name: str, status: str, worker_name: str, channel: str) -> None:
        """Send a formatted task notification to Slack"""
        status_emoji = {
            "pending": "⏳",
            "in_progress": "⚙️",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫"
        }
        
        emoji = status_emoji.get(status, "ℹ️")
        text = f"{emoji} Task Update: {task_name}"
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Task:* {task_name}\n*Status:* {status.replace('_', ' ').title()}\n*Worker:* {worker_name}\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
        ]
        
        await self.send_message(channel, text, blocks)
    
    async def send_worker_alert(self, worker_name: str, alert_type: str, message: str, channel: str) -> None:
        """Send a worker alert notification"""
        alert_emoji = {
            "offline": "🔴",
            "unhealthy": "🟡",
            "overloaded": "🟠",
            "recovered": "🟢"
        }
        
        emoji = alert_emoji.get(alert_type, "⚠️")
        text = f"{emoji} Worker Alert: {worker_name}"
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Worker:* {worker_name}\n*Alert:* {alert_type.title()}\n*Message:* {message}\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
        ]
        
        await self.send_message(channel, text, blocks)
    
    async def create_channel(self, channel_name: str, is_private: bool = False) -> Dict[str, Any]:
        """Create a new Slack channel"""
        try:
            async with aiohttp.ClientSession() as session:
                endpoint = "conversations.create"
                payload = {
                    "name": channel_name,
                    "is_private": is_private
                }
                
                async with session.post(
                    f"{self.base_url}/{endpoint}",
                    headers=self.headers,
                    json=payload
                ) as response:
                    result = await response.json()
                    if not result.get("ok"):
                        raise SlackServiceException(f"Failed to create channel: {result.get('error', 'Unknown error')}")
                    return result
        except aiohttp.ClientError as e:
            raise SlackServiceException(f"HTTP error creating channel: {str(e)}")
    
    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get information about a Slack channel"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/conversations.info",
                    headers=self.headers,
                    params={"channel": channel_id}
                ) as response:
                    result = await response.json()
                    if not result.get("ok"):
                        raise SlackServiceException(f"Failed to get channel info: {result.get('error', 'Unknown error')}")
                    return result
        except aiohttp.ClientError as e:
            raise SlackServiceException(f"HTTP error getting channel info: {str(e)}")
    
    async def upload_file(self, file_path: str, channels: List[str], title: Optional[str] = None) -> Dict[str, Any]:
        """Upload a file to Slack channels"""
        try:
            async with aiohttp.ClientSession() as session:
                with open(file_path, 'rb') as file:
                    data = aiohttp.FormData()
                    data.add_field('file', file, filename=file_path.split('/')[-1])
                    data.add_field('channels', ','.join(channels))
                    if title:
                        data.add_field('title', title)
                    
                    headers = {"Authorization": f"Bearer {self.bot_token}"}
                    
                    async with session.post(
                        f"{self.base_url}/files.upload",
                        headers=headers,
                        data=data
                    ) as response:
                        result = await response.json()
                        if not result.get("ok"):
                            raise SlackServiceException(f"Failed to upload file: {result.get('error', 'Unknown error')}")
                        return result
        except (aiohttp.ClientError, IOError) as e:
            raise SlackServiceException(f"Error uploading file: {str(e)}")