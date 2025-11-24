from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import uuid
from enum import Enum
from datetime import date
from enum import Enum


class LeaveType(str, Enum):
    SICK = "Sick"
    CASUAL = "Casual"
    EMERGENCY = "Emergency"


class LeaveStatus(str, Enum):
    APPROVED = "Approved"
    REJECTED = "Rejected"
    PENDING = "Pending"


class CreateLeaveRequest(BaseModel):
    leave_type: LeaveType
    from_date: date
    to_date: date
    days: int
    reason: str


class ApproveRejectRequest(BaseModel):
    status: LeaveStatus  # APPROVED / REJECTED
    comment: Optional[str] = None  # optional for approve, required for reject


class LeaveResponse(BaseModel):
    id: str
    leave_type: LeaveType
    from_date: date
    to_date: date
    days: int
    reason: str
    status: LeaveStatus
    mentor_id: str
    lead_id: str


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
