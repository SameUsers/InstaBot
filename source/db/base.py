from typing import Any
from sqlalchemy.orm import as_declarative, declared_attr

__all__ = ("BaseModel",)

@as_declarative()
class BaseModel:
    id: Any
    __name__: str
    __table_name__: str = None

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__table_name__ or cls.__name__.lower()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)