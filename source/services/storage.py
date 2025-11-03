import asyncio
import datetime
import uuid
import io
import json
from minio import Minio
import base64
from fastapi import UploadFile
from loguru import logger

from source.conf import settings

class MinioClient:
    def __init__(self):
        endpoint = f"{settings.minio_host}:{settings.minio_port}"
        self.client = Minio(
            endpoint,
            access_key=settings.minio_user,
            secret_key=settings.minio_password,
            secure=False
        )
        self.bucket_name = settings.minio_bucket
        self.public_url = settings.minio_public_url
        self._bucket_initialized = False
        self._init_lock = None

    async def _ensure_bucket_exists(self):
        """Ленивая инициализация bucket: проверка и создание при первом использовании."""
        if self._bucket_initialized:
            return
            
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()
        
        async with self._init_lock:
            if self._bucket_initialized:
                return
            
            try:
                logger.info("Checking if MinIO bucket exists: bucket={bucket_name}", bucket_name=self.bucket_name)
                bucket_exists = await asyncio.to_thread(
                    self.client.bucket_exists,
                    self.bucket_name
                )
                
                if not bucket_exists:
                    logger.info("Creating MinIO bucket: bucket={bucket_name}", bucket_name=self.bucket_name)
                    await asyncio.to_thread(
                        self.client.make_bucket,
                        self.bucket_name
                    )
                    
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": "*"},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                            }
                        ]
                    }
                    policy_json = json.dumps(policy)
                    await asyncio.to_thread(
                        self.client.set_bucket_policy,
                        self.bucket_name,
                        policy_json
                    )
                    logger.info("MinIO bucket created and configured: bucket={bucket_name}", bucket_name=self.bucket_name)
                else:
                    logger.info("MinIO bucket already exists: bucket={bucket_name}", bucket_name=self.bucket_name)
                
                self._bucket_initialized = True
            except Exception as e:
                logger.exception("Error creating MinIO bucket: bucket={bucket_name}, error={error}", 
                               bucket_name=self.bucket_name, error=str(e))
                raise RuntimeError(f"Error creating bucket: {e}")

    def _generate_filename(self, prefix: str, extension: str = "jpeg") -> str:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"

    def _build_public_url(self, filename: str) -> str:
        return f"{self.public_url}/{self.bucket_name}/{filename}"

    def _decode_base64(self, base64_string: str) -> bytes:
        if base64_string.startswith('data:'):
            base64_string = base64_string.split(',')[1]
        return base64.b64decode(base64_string)

    async def upload_from_base64(self, base64_string: str) -> str:
        if not base64_string or not base64_string.strip():
            raise ValueError("Base64 string cannot be empty")
        
        await self._ensure_bucket_exists()
        
        image_data = self._decode_base64(base64_string)
        filename = self._generate_filename("post", "jpeg")
        
        logger.info("Uploading file from base64: filename={filename}, size={size}", 
                   filename=filename, size=len(image_data))
        
        try:
            await asyncio.to_thread(
                self.client.put_object,
                bucket_name=self.bucket_name,
                object_name=filename,
                data=io.BytesIO(image_data),
                length=len(image_data),
                content_type="image/jpeg"
            )
            
            public_url = self._build_public_url(filename)
            logger.info("File uploaded successfully: filename={filename}, url={url}", 
                       filename=filename, url=public_url)
            return public_url
        except Exception as exc:
            logger.exception("Failed to upload file from base64: filename={filename}, error={error}", 
                           filename=filename, error=str(exc))
            raise

    def _get_file_extension(self, filename: str | None) -> str:
        if filename:
            return filename.split('.')[-1]
        return 'jpeg'

    async def upload_file(self, file: UploadFile) -> str:
        await self._ensure_bucket_exists()
        
        file_extension = self._get_file_extension(file.filename)
        filename = self._generate_filename("ref", file_extension)
        file_content = await file.read()
        content_type = file.content_type or f"image/{file_extension}"

        logger.info("Uploading file: filename={filename}, original_filename={original}, size={size}", 
                   filename=filename, original=file.filename, size=len(file_content))

        try:
            await asyncio.to_thread(
                self.client.put_object,
                bucket_name=self.bucket_name,
                object_name=filename,
                data=io.BytesIO(file_content),
                length=len(file_content),
                content_type=content_type
            )

            public_url = self._build_public_url(filename)
            logger.info("File uploaded successfully: filename={filename}, url={url}", 
                       filename=filename, url=public_url)
            return public_url
        except Exception as exc:
            logger.exception("Failed to upload file: filename={filename}, error={error}", 
                           filename=filename, error=str(exc))
            raise

minio_client = MinioClient()