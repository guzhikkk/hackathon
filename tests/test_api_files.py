"""Тесты API файлов — upload, download, delete, list."""

from unittest.mock import AsyncMock, patch

import pytest


# ─── Upload ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_file(client):
    """Загрузка файла — возвращает key и url."""
    with patch("app.api.files.s3_client") as mock_s3:
        mock_s3.upload_file = AsyncMock(return_value="abc123.txt")
        mock_s3.generate_presigned_url = AsyncMock(return_value="https://s3/abc123.txt")

        response = await client.post(
            "/api/files/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "abc123.txt"
    assert data["url"] == "https://s3/abc123.txt"
    assert data["filename"] == "test.txt"
    assert data["content_type"] == "text/plain"
    assert data["size"] == 11  # len(b"hello world")


@pytest.mark.asyncio
async def test_upload_file_with_folder(client):
    """Загрузка файла в папку."""
    with patch("app.api.files.s3_client") as mock_s3:
        mock_s3.upload_file = AsyncMock(return_value="photos/abc123.jpg")
        mock_s3.generate_presigned_url = AsyncMock(return_value="https://s3/photos/abc123.jpg")

        response = await client.post(
            "/api/files/upload?folder=photos",
            files={"file": ("photo.jpg", b"\xff\xd8\xff", "image/jpeg")},
        )

    assert response.status_code == 200
    assert response.json()["key"] == "photos/abc123.jpg"


@pytest.mark.asyncio
async def test_upload_file_too_large(client):
    """Файл больше лимита → 413."""
    with patch("app.api.files.MAX_FILE_SIZE", 10):  # лимит 10 байт
        response = await client.post(
            "/api/files/upload",
            files={"file": ("big.bin", b"x" * 20, "application/octet-stream")},
        )

    assert response.status_code == 413


# ─── Get / Download ──────────────────────────────────────


@pytest.mark.asyncio
async def test_get_file_presigned_url(client):
    """Получить presigned URL файла."""
    with patch("app.api.files.s3_client") as mock_s3:
        mock_s3.generate_presigned_url = AsyncMock(return_value="https://s3/signed")

        response = await client.get("/api/files/docs/file.pdf")

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "docs/file.pdf"
    assert data["url"] == "https://s3/signed"


@pytest.mark.asyncio
async def test_download_file(client):
    """Скачать файл напрямую (download=true)."""
    content = b"file content here"

    with patch("app.api.files.s3_client") as mock_s3:
        mock_s3.download_file = AsyncMock(return_value=content)

        response = await client.get("/api/files/test.txt?download=true")

    assert response.status_code == 200
    assert response.content == content


@pytest.mark.asyncio
async def test_get_file_not_found(client):
    """Несуществующий файл → 404."""
    with patch("app.api.files.s3_client") as mock_s3:
        mock_s3.generate_presigned_url = AsyncMock(side_effect=Exception("NoSuchKey"))

        response = await client.get("/api/files/nonexistent.txt")

    assert response.status_code == 404


# ─── Delete ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_file(client):
    """Удалить файл."""
    with patch("app.api.files.s3_client") as mock_s3:
        mock_s3.delete_file = AsyncMock()

        response = await client.delete("/api/files/old-file.txt")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


@pytest.mark.asyncio
async def test_delete_file_error(client):
    """Ошибка при удалении → 500."""
    with patch("app.api.files.s3_client") as mock_s3:
        mock_s3.delete_file = AsyncMock(side_effect=Exception("S3 error"))

        response = await client.delete("/api/files/broken.txt")

    assert response.status_code == 500


# ─── List ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_files(client):
    """Список файлов в bucket."""
    files_list = [
        {"key": "file1.txt", "size": 100, "last_modified": "2024-01-01T00:00:00"},
        {"key": "file2.txt", "size": 200, "last_modified": "2024-01-02T00:00:00"},
    ]

    with patch("app.api.files.s3_client") as mock_s3:
        mock_s3.list_files = AsyncMock(return_value=files_list)

        response = await client.get("/api/files")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["files"]) == 2


@pytest.mark.asyncio
async def test_list_files_with_prefix(client):
    """Фильтрация по префиксу."""
    with patch("app.api.files.s3_client") as mock_s3:
        mock_s3.list_files = AsyncMock(return_value=[])

        response = await client.get("/api/files?prefix=photos/")

    assert response.status_code == 200
    mock_s3.list_files.assert_called_once_with(prefix="photos/")


@pytest.mark.asyncio
async def test_list_files_empty(client):
    """Пустой bucket."""
    with patch("app.api.files.s3_client") as mock_s3:
        mock_s3.list_files = AsyncMock(return_value=[])

        response = await client.get("/api/files")

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["files"] == []
