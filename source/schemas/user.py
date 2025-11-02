from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

class UserBaseSchema(BaseModel):
    user_id: str = Field(...)
    email: EmailStr = Field(...)
    username: str = Field(...)
    permissions: str = Field(...)
    created_at: datetime = Field(...)
    model_config = ConfigDict(from_attributes=True)

class UserSchema(UserBaseSchema):
    hash_password: str = Field(..., exclude=True)
    refresh_token_version: int = Field(...)

class UserOutputSchema(UserBaseSchema):
    pass