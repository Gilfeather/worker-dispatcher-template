from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..exceptions import S3ServiceException


class S3Adapter:
    def __init__(
        self,
        region_name: str = "us-east-1",
        executor: Optional[ThreadPoolExecutor] = None,
    ):
        self.region_name = region_name
        self.executor = executor or ThreadPoolExecutor(max_workers=10)
        try:
            self.s3_client = boto3.client("s3", region_name=region_name)
        except NoCredentialsError:
            raise S3ServiceException("AWS credentials not found")

    async def upload_file(
        self, file_path: str, bucket_name: str, object_key: str
    ) -> str:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self.s3_client.upload_file,
                file_path,
                bucket_name,
                object_key,
            )
            return f"s3://{bucket_name}/{object_key}"
        except ClientError as e:
            raise S3ServiceException(f"Failed to upload file to S3: {str(e)}")

    async def download_file(
        self, bucket_name: str, object_key: str, file_path: str
    ) -> None:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self.s3_client.download_file,
                bucket_name,
                object_key,
                file_path,
            )
        except ClientError as e:
            raise S3ServiceException(f"Failed to download file from S3: {str(e)}")

    async def get_object(self, bucket_name: str, object_key: str) -> bytes:
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor, self.s3_client.get_object, bucket_name, object_key
            )
            return response["Body"].read()
        except ClientError as e:
            raise S3ServiceException(f"Failed to get object from S3: {str(e)}")

    async def put_object(self, bucket_name: str, object_key: str, data: bytes) -> str:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self.s3_client.put_object,
                Bucket=bucket_name,
                Key=object_key,
                Body=data,
            )
            return f"s3://{bucket_name}/{object_key}"
        except ClientError as e:
            raise S3ServiceException(f"Failed to put object to S3: {str(e)}")

    async def delete_object(self, bucket_name: str, object_key: str) -> None:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self.s3_client.delete_object,
                Bucket=bucket_name,
                Key=object_key,
            )
        except ClientError as e:
            raise S3ServiceException(f"Failed to delete object from S3: {str(e)}")

    async def list_objects(self, bucket_name: str, prefix: str = "") -> list:
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self.s3_client.list_objects_v2,
                Bucket=bucket_name,
                Prefix=prefix,
            )
            return response.get("Contents", [])
        except ClientError as e:
            raise S3ServiceException(f"Failed to list objects in S3: {str(e)}")

    async def object_exists(self, bucket_name: str, object_key: str) -> bool:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self.s3_client.head_object,
                Bucket=bucket_name,
                Key=object_key,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise S3ServiceException(
                f"Failed to check object existence in S3: {str(e)}"
            )

    async def generate_presigned_url(
        self, bucket_name: str, object_key: str, expiration: int = 3600
    ) -> str:
        try:
            loop = asyncio.get_event_loop()
            url = await loop.run_in_executor(
                self.executor,
                self.s3_client.generate_presigned_url,
                "get_object",
                {"Bucket": bucket_name, "Key": object_key},
                expiration,
            )
            return url
        except ClientError as e:
            raise S3ServiceException(f"Failed to generate presigned URL: {str(e)}")

    def close(self):
        if self.executor:
            self.executor.shutdown(wait=True)
