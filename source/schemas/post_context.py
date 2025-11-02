from pydantic import BaseModel, Field, ConfigDict, constr

class CreatePostBaseContext(BaseModel):
    content: constr(min_length=1, max_length=16000, strip_whitespace=True) = Field(...)
    model_config = ConfigDict(from_attributes=True)

class PostBaseContextResponse(BaseModel):
    message: str = Field(...)

class PostBaseContextGetResponse(BaseModel):
    content: str = Field(...)
