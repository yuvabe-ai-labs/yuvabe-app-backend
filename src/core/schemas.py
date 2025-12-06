from typing import Generic, TypeVar
from sqlmodel import SQLModel
from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    status_code: int
    data: T

class AppConfigResponse(SQLModel):
    version: str
    apk_download_link: str