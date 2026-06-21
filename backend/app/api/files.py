from fastapi import APIRouter, HTTPException, UploadFile, File, Query, status, Depends
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies.auth import CurrentUser, AdminUser
from app.dependencies.database import get_db
from app.services.s3 import s3_client
from app.models.file import FileRecord
from app.models.user import User

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("/upload")
async def upload_file(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
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

    
    file_record = FileRecord(key=key, owner_id=user.id)
    db.add(file_record)
    await db.commit()

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
    user: CurrentUser,
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
async def delete_file(
    key: str, 
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    
    result = await db.execute(select(FileRecord).where(FileRecord.key == key))
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File record not found in DB",
        )

    if file_record.owner_id != user.id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own files",
        )

    
    try:
        await s3_client.delete_file(key)
        await db.delete(file_record)
        await db.commit()
        return {"ok": True, "message": f"File '{key}' deleted"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}",
        )


@router.get("")
async def list_files(
    user: CurrentUser,
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
