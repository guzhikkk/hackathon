import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
import re


class UserDataSchema(BaseModel):
    full_name: str
    avatar_url: str | None = None

    @field_validator('avatar_url')
    @classmethod
    def validate_avatar(cls, v: str | None) -> str | None:
        if v and re.match(r"^(javascript|data|vbscript):", v.lower()):
            raise ValueError("Invalid URL scheme")
        return v

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    hashed_password: str
    full_name: str = ""
    avatar_url: str | None = None
    
    @field_validator('avatar_url')
    @classmethod
    def validate_avatar(cls, v: str | None) -> str | None:
        if v and re.match(r"^(javascript|data|vbscript):", v.lower()):
            raise ValueError("Invalid URL scheme")
        return v


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    is_admin: bool
    is_verified: bool
    created_at: datetime
    user_data: UserDataSchema | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None

    @field_validator('avatar_url')
    @classmethod
    def validate_avatar(cls, v: str | None) -> str | None:
        if v and re.match(r"^(javascript|data|vbscript):", v.lower()):
            raise ValueError("Invalid URL scheme")
        return v

class RoleUpdate(BaseModel):
    is_admin: bool
