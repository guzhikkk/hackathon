"""
Базовые классы и миксины для ORM моделей.

Используй IDMixin + TimestampMixin в своих моделях:

    class MyModel(IDMixin, TimestampMixin, Base):
        __tablename__ = "my_models"
        name: Mapped[str]
"""

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""
    pass


class IDMixin:
    """UUID primary key миксин."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )


class TimestampMixin:
    """Автоматические created_at / updated_at."""

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )
