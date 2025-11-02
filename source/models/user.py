from sqlalchemy import String, DateTime, func
from sqlalchemy import UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from source.db.base import BaseModel
from source.core.constants import Permissions

class User(BaseModel):
    user_id: Mapped[uuid.UUID] = mapped_column(
        SAUUID(),
        default=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    permissions: Mapped[str] = mapped_column(
        String(255),
        unique=False,
        default=Permissions.default
    )
    hash_password: Mapped[str]
    refresh_token_version: Mapped[int] = mapped_column(
        default=0
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
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None
    )