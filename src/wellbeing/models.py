from sqlmodel import Field, SQLModel, Relationship, ForeignKey,Column
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID

class WaterLogs(SQLModel, table=True):
    __tablename__ = "water_logs"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    amount_ml: int = Field(..., nullable=False)
    logged_at: datetime = Field(default_factory=datetime.now, nullable=False)
    goal_ml: Optional[int] = Field(default=None, nullable=True)
    recommended_ml: Optional[int] = Field(default=None, nullable=True)
    
    user: "Users" = Relationship(back_populates="water_logs")
