from pathlib import Path

import aioboto3
from botocore.exceptions import ClientError

from ..logger.get_logger import get_logger
from ..settings.settings import S3Settings

logger = get_logger(__name__)


class S3Client:
    def __init__(self, s3_settings: S3Settings):
        self.access_key = s3_settings.AWS_KEY_ID
        self.secret_key = s3_settings.AWS_SECRET_KEY
        self.region = s3_settings.REGION
        self.url = s3_settings.S3_URL
        self.bucket = s3_settings.S3_BUCKET

        self.session = aioboto3.Session()

    async def upload_file(self, file, key: str):
        async with self.session.client(
            "s3",
            endpoint_url=self.url,
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as s3:
            content = await file.read()

            try:
                await s3.put_object(Bucket=self.bucket, Key=key, Body=content, ContentType=file.content_type)
                logger.info("File was successfully uploaded to S3")
            except ClientError as e:
                logger.warning("Error while uploading file to s3: %s", e)
                raise e

    async def upload_file_from_fs(self, file_path: str, key: str):
        file = Path(file_path)

        async with self.session.client(
            "s3",
            endpoint_url=self.url,
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as s3:
            try:
                with file.open("rb") as f:
                    content = f.read()

                await s3.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=content,
                )

                logger.info("File was successfully uploaded to S3 from FS")

            except ClientError as e:
                logger.warning("Error while uploading file from FS to s3: %s", e)
                raise

    async def get_file(self, key: str) -> tuple[bytes, str]:
        async with self.session.client(
            "s3",
            endpoint_url=self.url,
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as s3:
            try:
                response = await s3.get_object(Bucket=self.bucket, Key=key)
                content = await response["Body"].read()
                logger.info("File was successfully retrieved from S3")
                return content, response.get("ContentType", "application/octet-stream")
            except ClientError as e:
                logger.warning("Error while getting file from s3: %s", e)
                raise e

    async def get_file_stream(self, key: str):
        return await self.get_file(key)

    async def delete_file(self, key: str):
        async with self.session.client(
            "s3",
            endpoint_url=self.url,
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as s3:
            try:
                await s3.delete_object(Bucket=self.bucket, Key=key)
                logger.info("File %s was successfully deleted from S3", key)
            except ClientError as e:
                logger.warning("Error while deleting file %s from s3: %s", key, e)
                raise e

    async def download_file(self, s3_key: str) -> bytes:
        content, _ = await self.get_file(s3_key)
        return content
