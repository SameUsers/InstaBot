from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy import UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid
from source.db.base import BaseModel

class Post(BaseModel):
    post_id: Mapped[uuid.UUID] = mapped_column(
        SAUUID(),
        default=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        SAUUID(),
        ForeignKey("user.user_id"),
        index=True,
        nullable=False
    )
    instagram_creation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    caption: Mapped[str] = mapped_column(String(4000), nullable=False)
    image_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    time_to_publish: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
