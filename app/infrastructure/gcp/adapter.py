from typing import Optional, Dict, Any, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage, bigquery, pubsub_v1
from google.cloud.exceptions import GoogleCloudError
import json

from ..exceptions import GCPServiceException


class GCPStorageAdapter:
    def __init__(self, project_id: str, executor: Optional[ThreadPoolExecutor] = None):
        self.project_id = project_id
        self.executor = executor or ThreadPoolExecutor(max_workers=10)
        try:
            self.client = storage.Client(project=project_id)
        except Exception as e:
            raise GCPServiceException(f"Failed to initialize GCP Storage client: {str(e)}")
    
    async def upload_blob(self, bucket_name: str, source_file_path: str, destination_blob_name: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            
            await loop.run_in_executor(
                self.executor,
                blob.upload_from_filename,
                source_file_path
            )
            return f"gs://{bucket_name}/{destination_blob_name}"
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to upload blob: {str(e)}")
    
    async def download_blob(self, bucket_name: str, source_blob_name: str, destination_file_path: str) -> None:
        try:
            loop = asyncio.get_event_loop()
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)
            
            await loop.run_in_executor(
                self.executor,
                blob.download_to_filename,
                destination_file_path
            )
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to download blob: {str(e)}")
    
    async def list_blobs(self, bucket_name: str, prefix: str = "") -> List[str]:
        try:
            loop = asyncio.get_event_loop()
            blobs = await loop.run_in_executor(
                self.executor,
                self.client.list_blobs,
                bucket_name,
                prefix
            )
            return [blob.name for blob in blobs]
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to list blobs: {str(e)}")
    
    async def delete_blob(self, bucket_name: str, blob_name: str) -> None:
        try:
            loop = asyncio.get_event_loop()
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            await loop.run_in_executor(
                self.executor,
                blob.delete
            )
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to delete blob: {str(e)}")


class GCPBigQueryAdapter:
    def __init__(self, project_id: str, executor: Optional[ThreadPoolExecutor] = None):
        self.project_id = project_id
        self.executor = executor or ThreadPoolExecutor(max_workers=10)
        try:
            self.client = bigquery.Client(project=project_id)
        except Exception as e:
            raise GCPServiceException(f"Failed to initialize BigQuery client: {str(e)}")
    
    async def query(self, query: str) -> List[Dict[str, Any]]:
        try:
            loop = asyncio.get_event_loop()
            query_job = await loop.run_in_executor(
                self.executor,
                self.client.query,
                query
            )
            results = await loop.run_in_executor(
                self.executor,
                query_job.result
            )
            return [dict(row) for row in results]
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to execute query: {str(e)}")
    
    async def insert_rows(self, table_id: str, rows: List[Dict[str, Any]]) -> None:
        try:
            loop = asyncio.get_event_loop()
            table = self.client.get_table(table_id)
            errors = await loop.run_in_executor(
                self.executor,
                self.client.insert_rows_json,
                table,
                rows
            )
            if errors:
                raise GCPServiceException(f"Failed to insert rows: {errors}")
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to insert rows: {str(e)}")
    
    async def create_table(self, table_id: str, schema: List[bigquery.SchemaField]) -> None:
        try:
            loop = asyncio.get_event_loop()
            table = bigquery.Table(table_id, schema=schema)
            await loop.run_in_executor(
                self.executor,
                self.client.create_table,
                table
            )
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to create table: {str(e)}")


class GCPPubSubAdapter:
    def __init__(self, project_id: str):
        self.project_id = project_id
        try:
            self.publisher = pubsub_v1.PublisherClient()
            self.subscriber = pubsub_v1.SubscriberClient()
        except Exception as e:
            raise GCPServiceException(f"Failed to initialize Pub/Sub clients: {str(e)}")
    
    async def publish_message(self, topic_name: str, message: Dict[str, Any]) -> str:
        try:
            topic_path = self.publisher.topic_path(self.project_id, topic_name)
            message_data = json.dumps(message).encode('utf-8')
            
            loop = asyncio.get_event_loop()
            future = await loop.run_in_executor(
                None,
                self.publisher.publish,
                topic_path,
                message_data
            )
            return future.result()
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to publish message: {str(e)}")
    
    async def create_subscription(self, topic_name: str, subscription_name: str) -> str:
        try:
            topic_path = self.publisher.topic_path(self.project_id, topic_name)
            subscription_path = self.subscriber.subscription_path(self.project_id, subscription_name)
            
            loop = asyncio.get_event_loop()
            subscription = await loop.run_in_executor(
                None,
                self.subscriber.create_subscription,
                request={"name": subscription_path, "topic": topic_path}
            )
            return subscription.name
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to create subscription: {str(e)}")
    
    async def pull_messages(self, subscription_name: str, max_messages: int = 10) -> List[Dict[str, Any]]:
        try:
            subscription_path = self.subscriber.subscription_path(self.project_id, subscription_name)
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.subscriber.pull,
                request={"subscription": subscription_path, "max_messages": max_messages}
            )
            
            messages = []
            for received_message in response.received_messages:
                message_data = json.loads(received_message.message.data.decode('utf-8'))
                messages.append({
                    "data": message_data,
                    "message_id": received_message.message.message_id,
                    "ack_id": received_message.ack_id
                })
            
            return messages
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to pull messages: {str(e)}")
    
    async def acknowledge_messages(self, subscription_name: str, ack_ids: List[str]) -> None:
        try:
            subscription_path = self.subscriber.subscription_path(self.project_id, subscription_name)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.subscriber.acknowledge,
                request={"subscription": subscription_path, "ack_ids": ack_ids}
            )
        except GoogleCloudError as e:
            raise GCPServiceException(f"Failed to acknowledge messages: {str(e)}")


class GCPAdapter:
    def __init__(self, project_id: str, executor: Optional[ThreadPoolExecutor] = None):
        self.project_id = project_id
        self.storage = GCPStorageAdapter(project_id, executor)
        self.bigquery = GCPBigQueryAdapter(project_id, executor)
        self.pubsub = GCPPubSubAdapter(project_id)
    
    def close(self):
        if hasattr(self.storage, 'executor') and self.storage.executor:
            self.storage.executor.shutdown(wait=True)
        if hasattr(self.bigquery, 'executor') and self.bigquery.executor:
            self.bigquery.executor.shutdown(wait=True)