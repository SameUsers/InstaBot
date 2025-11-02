import datetime
import uuid
import io
import json
from minio import Minio
import base64
from fastapi import UploadFile

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
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
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
                self.client.set_bucket_policy(self.bucket_name, policy_json)
        except Exception as e:
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
        image_data = self._decode_base64(base64_string)
        filename = self._generate_filename("post", "jpeg")
        
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=filename,
            data=io.BytesIO(image_data),
            length=len(image_data),
            content_type="image/jpeg"
        )
        
        return self._build_public_url(filename)

    def _get_file_extension(self, filename: str | None) -> str:
        if filename:
            return filename.split('.')[-1]
        return 'jpeg'

    async def upload_file(self, file: UploadFile) -> str:
        file_extension = self._get_file_extension(file.filename)
        filename = self._generate_filename("ref", file_extension)
        file_content = await file.read()
        content_type = file.content_type or f"image/{file_extension}"

        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=filename,
            data=io.BytesIO(file_content),
            length=len(file_content),
            content_type=content_type
        )

        return self._build_public_url(filename)

minio_client = MinioClient()