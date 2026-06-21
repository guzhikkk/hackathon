import uuid
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserData
from app.models.file import FileRecord
from app.schemas.user import UserCreate, UserUpdate
from app.services.s3 import s3_client
import logging

logger = logging.getLogger(__name__)


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    user = User(
        email=data.email, 
        hashed_password=data.hashed_password
    )
    user.user_data = UserData()
    if data.full_name is not None:
        user.user_data.full_name = data.full_name
    if data.avatar_url is not None:
        user.user_data.avatar_url = str(data.avatar_url)
    session.add(user)
    await session.commit()
    return await get_user_by_id(session, user.id)


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(
        select(User).options(joinedload(User.user_data)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(
        select(User).options(joinedload(User.user_data)).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User)
        .options(joinedload(User.user_data))
        .order_by(User.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


async def update_user(
    session: AsyncSession,
    user: User,
    data: UserUpdate,
) -> User:
    update_data = data.model_dump(exclude_unset=True, mode="json")
    
    old_avatar = user.user_data.avatar_url if user.user_data else None
    
    if not user.user_data:
        user.user_data = UserData(user_id=user.id)

    for field, value in update_data.items():
        setattr(user.user_data, field, value)
        
    await session.commit()
    
    if "avatar_url" in update_data and old_avatar and old_avatar != update_data["avatar_url"]:
        result = await session.execute(select(UserData).where(UserData.avatar_url == old_avatar))
        users_with_old_avatar = result.scalars().all()
        
        if len(users_with_old_avatar) == 0:
            file_records_result = await session.execute(select(FileRecord).where(FileRecord.owner_id == user.id))
            user_files = file_records_result.scalars().all()
            
            file_to_delete = None
            for f in user_files:
                if f.key in old_avatar:
                    file_to_delete = f
                    break
            
            if file_to_delete:
                try:
                    await s3_client.delete_file(file_to_delete.key)
                    await session.delete(file_to_delete)
                    await session.commit()
                except Exception as e:
                    logger.error(f"Failed to GC old avatar {old_avatar}: {e}")

    return await get_user_by_id(session, user.id)


async def delete_user(session: AsyncSession, user: User) -> None:
    result = await session.execute(select(FileRecord).where(FileRecord.owner_id == user.id))
    files_to_delete = result.scalars().all()
    
    for f in files_to_delete:
        try:
            await s3_client.delete_file(f.key)
        except Exception as e:
            logger.error(f"Failed to delete file {f.key} from S3 during user {user.id} deletion: {e}")
            
    await session.delete(user)
    await session.commit()
