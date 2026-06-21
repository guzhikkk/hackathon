import uuid
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin


class UserData(IDMixin, TimestampMixin, Base):
    __tablename__ = "user_data"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(
        String(255), default="", server_default=""
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="user_data")


class User(IDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(1024), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    user_data: Mapped["UserData"] = relationship(
        "UserData", back_populates="user", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
