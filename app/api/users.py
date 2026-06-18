from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import CurrentUser
from app.dependencies.database import get_db

from app.schemas.user import UserRead, UserUpdate
from app.services.user import get_user_by_id, get_users, update_user, delete_user

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    data: UserUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    updated = await update_user(db, user, data)
    return updated


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await delete_user(db, user)


@router.get("", response_model=list[UserRead])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    users = await get_users(db)
    return users


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
