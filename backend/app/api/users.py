from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import CurrentUser, AdminUser
from app.dependencies.database import get_db

from app.schemas.user import UserRead, UserUpdate
from app.services.user import get_user_by_id, get_users, update_user, delete_user

router = APIRouter()

@router.get("/me", response_model=UserRead)
async def get_current_user_profile(user: CurrentUser):
    return user


from sqlalchemy import select
from app.models.file import FileRecord
from app.services.s3 import s3_client
from app.models.user import UserData

@router.patch("/me", response_model=UserRead)
async def update_current_user(
    data: UserUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    old_avatar = user.user_data.avatar_url if user.user_data else None

    updated = await update_user(db, user, data)
    
    
    update_dict = data.model_dump(exclude_unset=True)
    if "avatar_url" in update_dict and old_avatar and old_avatar != data.avatar_url:
        
        result = await db.execute(select(UserData).where(UserData.avatar_url == old_avatar))
        users_with_old_avatar = result.scalars().all()
        
        if len(users_with_old_avatar) == 0:
            
            file_record_result = await db.execute(select(FileRecord).where(FileRecord.key == old_avatar))
            file_record = file_record_result.scalar_one_or_none()
            
            if file_record:
                try:
                    await s3_client.delete_file(file_record.key)
                    await db.delete(file_record)
                    await db.commit()
                except Exception as e:
                    print(f"Failed to GC old avatar {old_avatar}: {e}")

    return updated


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await delete_user(db, user)


@router.get("", response_model=list[UserRead])
async def list_users(
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    users = await get_users(db)
    return users


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def admin_update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    updated = await update_user(db, user, data)
    return updated


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: uuid.UUID,
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    await delete_user(db, user)


class RoleUpdate(BaseModel):
    is_admin: bool


@router.patch("/{user_id}/role", response_model=UserRead)
async def update_user_role(
    user_id: uuid.UUID,
    data: RoleUpdate,
    admin: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.is_admin = data.is_admin
    await db.commit()
    await db.refresh(user)
    return user
