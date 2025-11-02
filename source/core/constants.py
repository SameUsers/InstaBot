from enum import StrEnum

class AccessTokenRows(StrEnum):
    sub = "sub"
    sub_email = "email"
    username = "username"
    permissions = "perms"
    exp = "exp"

class RefreshTokenRows(StrEnum):
    sub = "sub"
    token_version = "ver"
    exp = "exp"

class Permissions(StrEnum):
    default = "default"
    premium = "premium"

class MessageRole(StrEnum):
    system = "system"
    user = "user"

class ContentType(StrEnum):
    text = "text"
    image_url = "image_url"

class ResponseKeys(StrEnum):
    error = "error"
    details = "details"
    text = "text"
    image_url = "image_url"

class ApiResponseKeys(StrEnum):
    choices = "choices"
    message = "message"
    content = "content"
    images = "images"
    image_url = "image_url"
    url = "url"

class PromptSuffixes(StrEnum):
    max_900_chars = "\n Текстовый ответ не более 500 символов. И не должен содержать Markdown."
    max_2000_chars = "\n Текстовый ответ не более 1800 символов. И не должен содержать Markdown. В конце каддого поста делай призыв к действию. Например протестируйте на вашем бизнесе, сократите затраты. Без слов купи и так далее. Используй рекмендуемые слова такие как - свяжизь, напиши, позвони, запроси демо"

