from pydantic import BaseModel, EmailStr, Field, ConfigDict, constr

class RegistrationSchema(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=32) = Field(...)
    email: EmailStr = Field(...)
    password: constr(min_length=6, max_length=64) = Field(...)
    model_config = ConfigDict(from_attributes=True)

class LoginSchema(BaseModel):
    email: EmailStr = Field(...)
    password: constr(min_length=6, max_length=64) = Field(...)
    model_config = ConfigDict(from_attributes=True)

class RegistrationSchemaResponse(BaseModel):
    access_token: str = Field(...)
    refresh_token: str = Field(...)
    model_config = ConfigDict(from_attributes=True)

class RefreshResponseSchema(BaseModel):
    access_token: str = Field(...)
    refresh_token: str = Field(...)
    model_config = ConfigDict(from_attributes=True)

class CurrentUserSchema(BaseModel):
    user_id: str = Field(...)
    email: EmailStr = Field(...)
    username: str = Field(...)
    permissions: str = Field(...)
    model_config = ConfigDict(from_attributes=True)