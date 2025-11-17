from typing import Optional
from pydantic import BaseModel
import uuid
from enum import Enum

class AssetStatus(str, Enum):
    ACTIVE = "Active"
    UNAVAILABLE = "Unavailable"
    ON_REQUEST = "On Request"
    IN_SERVICE = "In Service"

class AssetCreateRequest(BaseModel):
    name: str
    type: str
    status: Optional[AssetStatus] = AssetStatus.UNAVAILABLE

class AssetUpdateRequest(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[AssetStatus] = None

class AssetResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: str
    status: AssetStatus

class BaseResponse(BaseModel):
    code: int
    data: dict
