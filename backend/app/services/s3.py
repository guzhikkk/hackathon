import uuid
from io import BytesIO
from typing import BinaryIO
import aioboto3
from app.config import get_settings

settings = get_settings()


class S3Client:
    def __init__(self):
        self.session = aioboto3.Session()
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket_name = settings.S3_BUCKET_NAME
        self.region = settings.S3_REGION

    def _get_client_kwargs(self) -> dict:
        return {
            "service_name": "s3",
            "endpoint_url": self.endpoint_url,
            "aws_access_key_id": self.access_key,
            "aws_secret_access_key": self.secret_key,
            "region_name": self.region,
        }

    async def ensure_bucket(self) -> None:
        async with self.session.client(**self._get_client_kwargs()) as client:
            try:
                await client.head_bucket(Bucket=self.bucket_name)
            except Exception:
                await client.create_bucket(Bucket=self.bucket_name)

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "",
    ) -> str:
        
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
        key = f"{folder}/{unique_name}" if folder else unique_name

        async with self.session.client(**self._get_client_kwargs()) as client:
            await client.upload_fileobj(
                file,
                self.bucket_name,
                key,
                ExtraArgs={"ContentType": content_type},
            )

        return key

    async def download_file(self, key: str) -> bytes:
        async with self.session.client(**self._get_client_kwargs()) as client:
            response = await client.get_object(
                Bucket=self.bucket_name, Key=key
            )
            data = await response["Body"].read()
            return data

    async def delete_file(self, key: str) -> None:
        async with self.session.client(**self._get_client_kwargs()) as client:
            await client.delete_object(
                Bucket=self.bucket_name, Key=key
            )

    async def generate_presigned_url(
        self, key: str, expires_in: int = 3600
    ) -> str:
        async with self.session.client(**self._get_client_kwargs()) as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            
            if url.startswith(self.endpoint_url):
                url = url.replace(self.endpoint_url, "", 1)
                
            return url

    async def list_files(self, prefix: str = "") -> list[dict]:
        async with self.session.client(**self._get_client_kwargs()) as client:
            response = await client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )
            files = []
            for obj in response.get("Contents", []):
                files.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                })
            return files

s3_client = S3Client()
