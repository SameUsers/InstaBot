from datetime import datetime
import uuid
from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from source.db.base import BaseModel

class InstagramCredentials(BaseModel):
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.user_id"),
        primary_key=True,
        index=True,
        nullable=False
    )
    instagram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    instagram_token: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )