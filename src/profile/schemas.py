from pydantic import BaseModel, EmailStr ,Field
from typing import Optional,List
import uuid
from enum import Enum
from datetime import date


class ApplyLeaveRequest(BaseModel):
    leave_type: str
    from_date: date
    to_date: date
    reason: Optional[str] = None

class ApproveRejectRequest(BaseModel):
    comment: Optional[str] = None
    reject_reason: Optional[str] = None  # used for reject endpoint

class LeaveResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    mentor_id: uuid.UUID
    lead_id: uuid.UUID
    leave_type: str
    from_date: date
    to_date: date
    days: int
    reason: Optional[str]
    status: str
    approved_by: Optional[uuid.UUID]
    approved_at: Optional[str]
    reject_reason: Optional[str]
    comment: Optional[str]

class BalanceResponse(BaseModel):
    leave_type: str
    limit: int
    used: int
    remaining: int

class DeviceTokenIn(BaseModel):
    device_token: str
    device_type: Optional[str] = None



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
