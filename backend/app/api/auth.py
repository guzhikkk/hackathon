import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.config import get_settings
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
)
from app.services.auth import (
    verify_verification_token,
    register_user_logic,
    authenticate_user_logic,
    refresh_token_logic
)
from app.services.user import get_user_by_id
from pydantic import BaseModel

router = APIRouter()
settings = get_settings()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/api", 
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth/refresh",
    )

def clear_auth_cookies(response: Response):
    response.delete_cookie(key="access_token", path="/api")
    response.delete_cookie(key="refresh_token", path="/api/auth/refresh")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tokens = await register_user_logic(data, db, background_tasks)
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return {"access_token": tokens["access_token"], "token_type": "bearer"}


@router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tokens = await authenticate_user_logic(data.email, data.password, db)
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return {"access_token": tokens["access_token"], "token_type": "bearer"}


@router.post("/token")
async def token(
    response: Response,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tokens = await authenticate_user_logic(form.username, form.password, db)
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return {"access_token": tokens["access_token"], "token_type": "bearer"}


@router.post("/refresh")
async def refresh(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie()] = None,
):
    tokens = await refresh_token_logic(refresh_token, db)
    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return {"access_token": tokens["access_token"], "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


class VerifyEmailRequest(BaseModel):
    token: str

@router.post("/verify-email")
async def verify_email(
    data: VerifyEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    payload = verify_verification_token(data.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    user_id = payload.get("sub")
    user = await get_user_by_id(db, uuid.UUID(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_verified:
        return {"message": "Email is already verified"}

    user.is_verified = True
    await db.commit()
    
    return {"message": "Email successfully verified"}
