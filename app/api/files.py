from fastapi import APIRouter, HTTPException, UploadFile, File, Query, status
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.services.s3 import s3_client

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Query("", description="Папка в bucket"),
):
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // 1024 // 1024} MB",
        )

    file_obj = BytesIO(contents)
    try:
        key = await s3_client.upload_file(
            file=file_obj,
            filename=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            folder=folder,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )

    url = await s3_client.generate_presigned_url(key)

    return {
        "key": key,
        "url": url,
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
    }


@router.get("/{key:path}")
async def get_file(
    key: str,
    download: bool = Query(False, description="Скачать файл напрямую"),
):
    if download:
        try:
            data = await s3_client.download_file(key)
            return StreamingResponse(
                BytesIO(data),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename={key.split('/')[-1]}"
                },
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {str(e)}",
            )
    else:
        try:
            url = await s3_client.generate_presigned_url(key)
            return {"key": key, "url": url}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {str(e)}",
            )


@router.delete("/{key:path}")
async def delete_file(key: str):
    try:
        await s3_client.delete_file(key)
        return {"ok": True, "message": f"File '{key}' deleted"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}",
        )


@router.get("")
async def list_files(
    prefix: str = Query("", description="Фильтр по префиксу"),
):
    """Список файлов в bucket."""
    try:
        files = await s3_client.list_files(prefix=prefix)
        return {"files": files, "total": len(files)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}",
        )
