"""
S3/MinIO клиент — загрузка, скачивание, удаление файлов.

Использование:
    from app.services.s3 import s3_client

    url = await s3_client.upload_file(file.file, file.filename, file.content_type)
    await s3_client.delete_file("path/to/file.jpg")
"""

import uuid
from io import BytesIO
from typing import BinaryIO

import aioboto3

from app.config import get_settings

settings = get_settings()


class S3Client:
    """Async обёртка над S3/MinIO."""

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
        """Создать bucket если не существует."""
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
        """
        Загрузить файл в S3.

        Args:
            file: Файловый объект (BytesIO или UploadFile.file)
            filename: Имя файла
            content_type: MIME тип
            folder: Папка в bucket (опционально)

        Returns:
            Ключ файла в S3 (path)
        """
        # Генерируем уникальный ключ
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
        """Скачать файл из S3."""
        async with self.session.client(**self._get_client_kwargs()) as client:
            response = await client.get_object(
                Bucket=self.bucket_name, Key=key
            )
            data = await response["Body"].read()
            return data

    async def delete_file(self, key: str) -> None:
        """Удалить файл из S3."""
        async with self.session.client(**self._get_client_kwargs()) as client:
            await client.delete_object(
                Bucket=self.bucket_name, Key=key
            )

    async def generate_presigned_url(
        self, key: str, expires_in: int = 3600
    ) -> str:
        """
        Создать presigned URL для прямого доступа к файлу.

        Args:
            key: Ключ файла в S3
            expires_in: Время жизни URL в секундах (default: 1 час)
        """
        async with self.session.client(**self._get_client_kwargs()) as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            return url

    async def list_files(self, prefix: str = "") -> list[dict]:
        """Список файлов в bucket с опциональным префиксом."""
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


# Синглтон клиента
s3_client = S3Client()
