import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class AssetStatus(str, Enum):
    ACTIVE = "Active"
    UNAVAILABLE = "Unavailable"
    ON_REQUEST = "On Request"
    IN_SERVICE = "In Service"


class Users(SQLModel, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email_id: str = Field(unique=True, nullable=False)
    password: str = Field(nullable=False)
    user_name: str = Field(nullable=False)
    is_verified: bool = Field(
        default=False, sa_column_kwargs={"server_default": "false"}
    )
    verification_token: Optional[str] = None
    verification_expires_at: Optional[datetime] = None
    dob: Optional[date] = None
    address: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    asset: List["Assets"] = Relationship(back_populates="user")


class Teams(SQLModel, table=True):
    __tablename__ = "teams"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, nullable=False)


class Roles(SQLModel, table=True):
    __tablename__ = "roles"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, nullable=False)


class UserTeamsRole(SQLModel, table=True):
    __tablename__ = "user_teams_role"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    team_id: uuid.UUID = Field(foreign_key="teams.id", nullable=False)
    role_id: uuid.UUID = Field(foreign_key="roles.id", nullable=False)


class Assets(SQLModel, table=True):
    __tablename__ = "assets"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    name: str = Field(nullable=False)
    type: str = Field(nullable=False)
    status: AssetStatus = Field(default=AssetStatus.UNAVAILABLE)
    user: "Users" = Relationship(back_populates="asset")


class EmotionLogs(SQLModel, table=True):
    __tablename__ = "emotion_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "log_date"),
        CheckConstraint("morning_emotion BETWEEN 1 AND 7 or morning_emotion IS NULL"),
        CheckConstraint("evening_emotion BETWEEN 1 AND 7 or evening_emotion IS NULL"),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    morning_emotion: Optional[int] = Field(default=None, ge=1, le=7)
    evening_emotion: Optional[int] = Field(default=None, ge=1, le=7)
    log_date: date = Field(default_factory=date.today)
