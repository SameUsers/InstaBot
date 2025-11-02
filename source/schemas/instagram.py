from pydantic import BaseModel, ConfigDict, Field, PositiveInt, constr

class CreateInstagramCredentials(BaseModel):
    instagram_id: PositiveInt = Field(...)
    instagram_token: constr(min_length=16, max_length=256, strip_whitespace=True) = Field(...)
    model_config = ConfigDict(from_attributes=True)

class BaseMessageResponse(BaseModel):
    message: str = Field(...)

class Sender(BaseModel):
    id: str

class Recipient(BaseModel):
    id: str

class Message(BaseModel):
    mid: str
    text: str | None = None

class MessageEdit(BaseModel):
    mid: str
    num_edit: int
    text: str | None = None

class MessagingItem(BaseModel):
    sender: Sender
    recipient: Recipient
    timestamp: int
    message: Message | None = None
    message_edit: MessageEdit | None = None

class Entry(BaseModel):
    time: int
    id: str
    messaging: list[MessagingItem]

class InstagramWebhookPayload(BaseModel):
    object: str
    entry: list[Entry]

class CreatePostRequest(BaseModel):
    image_url: list[str]
    caption: str

class InstagramCredentialsResponse(BaseModel):
    instagram_id: int = Field(...)
    instagram_token: str = Field(...)

class PreparePostResponse(BaseModel):
    post_id: str = Field(...)
    image_url: str = Field(...)
    caption: str = Field(...)
    creation_id: str = Field(...)

class PublishPostRequest(BaseModel):
    post_id: str = Field(...)
