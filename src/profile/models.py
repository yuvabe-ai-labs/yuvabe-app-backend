from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Column, String
import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, Relationship, SQLModel, ForeignKey

class LeaveType(str, Enum):
    SICK = "Sick"
    CASUAL = "Casual"
    EMERGENCY = "Emergency"

class LeaveStatus(str, Enum):
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"
    PENDING = "Pending"

class Leave(SQLModel, table=True):
    __tablename__ = "leave"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False
        )
    )
    mentor_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True
        )
    )
    lead_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True
        )
    )
    leave_type: LeaveType = Field(default=LeaveType.SICK)
    from_date: date = Field(nullable=False)
    to_date: date = Field(nullable=False)
    days: Optional[int] = 1
    reason: str = Field(nullable=True)
    status: LeaveStatus = Field(default=LeaveStatus.PENDING)
    is_delivered: bool = Field(default= False)
    is_read: bool = Field(default=False)
    requested_at: date = Field(default_factory=date.today)
    updated_at: date = Field(default_factory=date.today)
    reject_reason: Optional[str] = None

class UserDevices(SQLModel, table=True):
    __tablename__ = "user_devices"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False
        )
    )
    device_token: str
    last_seen: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
