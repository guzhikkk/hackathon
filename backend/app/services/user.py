import uuid
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserData
from app.schemas.user import UserCreate, UserUpdate


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    user = User(
        email=data.email, 
        hashed_password=data.hashed_password
    )
    user_data = UserData(
        full_name=data.full_name,
        avatar_url=data.avatar_url
    )
    user.user_data = user_data
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
    update_data = data.model_dump(exclude_unset=True)
    
    if not user.user_data:
        user.user_data = UserData(user_id=user.id)

    for field, value in update_data.items():
        setattr(user.user_data, field, value)
        
    await session.commit()
    return await get_user_by_id(session, user.id)


async def delete_user(session: AsyncSession, user: User) -> None:
    await session.delete(user)
    await session.commit()
