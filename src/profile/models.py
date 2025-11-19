import uuid
from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum


class LeaveStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Leaves(SQLModel, table=True):
    __tablename__ = "leaves"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Foreign keys (users table)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    mentor_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    lead_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)

    leave_type: str = Field(nullable=False)
    from_date: date = Field(nullable=False)
    to_date: date = Field(nullable=False)
    days: int = Field(nullable=False)
    reason: Optional[str] = None

    status: LeaveStatus = Field(default=LeaveStatus.PENDING)

    approved_by: Optional[uuid.UUID] = Field(foreign_key="users.id", default=None)
    approved_at: Optional[datetime] = None
    reject_reason: Optional[str] = None

    comment: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
