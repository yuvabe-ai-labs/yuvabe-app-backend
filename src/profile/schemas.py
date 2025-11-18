from pydantic import BaseModel, EmailStr
from typing import Optional
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


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    dob: Optional[str] = None
    address: Optional[str] = None

    current_password: Optional[str] = None
    new_password: Optional[str] = None


class SendMailRequest(BaseModel):
    user_id: str
    to: EmailStr
    subject: str
    body: str
    from_name: Optional[str] = None
