import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column
from sqlmodel import SQLModel, Field, ForeignKey


class PayslipStatus(str, Enum):
    PENDING = "Pending"
    SENT = "Sent"
    FAILED = "Failed"


class PayslipRequest(SQLModel, table=True):
    __tablename__ = "payslip_requests"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    user_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    requested_at: datetime = Field(default_factory=datetime.now)

    status: PayslipStatus = Field(default=PayslipStatus.PENDING)

    refresh_token: Optional[str] = None

    error_message: Optional[str] = None
