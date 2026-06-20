import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserDataSchema(BaseModel):
    full_name: str
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    hashed_password: str
    full_name: str = ""
    avatar_url: str | None = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    user_data: UserDataSchema | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
