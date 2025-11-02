from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy import UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid
from source.db.base import BaseModel

class PostBase(BaseModel):
    user_id: Mapped[uuid.UUID] = mapped_column(
        SAUUID(),
        ForeignKey("user.user_id"),
        primary_key=True,
        index=True,
        nullable=False
    )
    content: Mapped[str] = mapped_column(
        String(16000),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )