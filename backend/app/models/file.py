import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin
from app.models.user import User


class FileRecord(IDMixin, TimestampMixin, Base):
    __tablename__ = "file_records"

    key: Mapped[str] = mapped_column(
        String(2048), unique=True, index=True, nullable=False
    )
    
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    owner: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<FileRecord {self.key}>"
