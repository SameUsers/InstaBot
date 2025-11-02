from pydantic import BaseModel, Field, ConfigDict
from typing import List
from uuid import UUID
from datetime import datetime

class CreatePostRecordRequest(BaseModel):
    instagram_creation_id: str = Field(...)
    caption: str = Field(...)
    image_url: str = Field(...)

class PostResponse(BaseModel):
    post_id: UUID = Field(...)
    instagram_creation_id: str = Field(...)
    caption: str = Field(...)
    image_url: str = Field(...)
    published_at: datetime | None = Field(default=None)
    time_to_publish: datetime | None = Field(default=None)
    model_config = ConfigDict(from_attributes=True)

class PostsListResponse(BaseModel):
    items: List[PostResponse]

class PublishByCreationIdRequest(BaseModel):
    creation_id: str = Field(...)

class SetTimeToPublishRequest(BaseModel):
    post_id: UUID = Field(...)
    time_to_publish: datetime = Field(...)
