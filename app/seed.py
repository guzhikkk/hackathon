import asyncio
from app.database import async_session_maker
from app.models.user import User
from app.services.auth import hash_password

ADMIN_EMAIL = "admin"

async def seed():
    async with async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            return

        admin = User(
            email=ADMIN_EMAIL,
            hashed_password=hash_password("admin"),
            full_name="admin",
            is_admin=True,
            is_active=True
        )
        session.add(admin)
        await session.commit()
        
if __name__ == "__main__":
    asyncio.run(seed())
