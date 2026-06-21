from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt
from app.config import get_settings
from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserCreate
from app.services.user import create_user, get_user_by_email, get_user_by_id
from app.services.email import send_email_async
import uuid

settings = get_settings()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: str, extra_data: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }
    if extra_data:
        payload.update(extra_data)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_token_pair(user_id: str) -> dict:
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None


def verify_access_token(token: str) -> dict | None:
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> dict | None:
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None

def create_verification_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "verify",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_verification_token(token: str) -> dict | None:
    payload = decode_token(token)
    if payload and payload.get("type") == "verify":
        return payload
    return None


async def register_user_logic(data: RegisterRequest, db: AsyncSession, background_tasks: BackgroundTasks) -> dict:
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await create_user(
        db,
        UserCreate(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        ),
    )

    verify_token = create_verification_token(str(user.id))
    verify_url = f"http://localhost/?verify={verify_token}"
    email_body = f"Здравствуйте, {data.full_name}!\n\nПожалуйста, подтвердите вашу электронную почту, перейдя по ссылке:\n{verify_url}\n\nСпасибо!"
    
    background_tasks.add_task(
        send_email_async,
        to_email=user.email,
        subject="Verify your email address",
        body=email_body,
    )

    return create_token_pair(str(user.id))

async def authenticate_user_logic(email: str, password: str, db: AsyncSession) -> dict:
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is linked to Google. Please sign in with Google.",
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return create_token_pair(str(user.id))

async def refresh_token_logic(refresh_token: str | None, db: AsyncSession) -> dict:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing in cookies",
        )

    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await get_user_by_id(db, uuid.UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return create_token_pair(str(user.id))

import httpx

async def authenticate_google_user_logic(code: str, db: AsyncSession) -> dict:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            },
        )
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to get Google token: {token_response.text}")
        
        access_token = token_response.json().get("access_token")

        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Google user info")
        
        userinfo = userinfo_response.json()
        email = userinfo.get("email")
        name = userinfo.get("name")
        picture = userinfo.get("picture")

        if not email:
            raise HTTPException(status_code=400, detail="Google account has no email")

        user = await get_user_by_email(db, email)
        if not user:
            from app.models.user import User, UserData
            user = User(email=email)
            user.user_data = UserData(full_name=name or "", avatar_url=picture)
            user.is_verified = True
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            pass

        return create_token_pair(str(user.id))