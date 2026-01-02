from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from typing import Optional


class WaterLogs(SQLModel, table=True):
    __tablename__ = "water_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    user_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    # Water (manual)
    amount_ml: Optional[int] = Field(default=None)

    # Steps (auto)
    steps_count: Optional[int] = Field(default=None)

    # Single timestamp (UPDATED on every water OR steps update)
    logged_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Goals
    goal_ml: Optional[int] = Field(default=None)
    recommended_ml: Optional[int] = Field(default=None)

    user: "Users" = Relationship(back_populates="water_logs")
