import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import UniqueConstraint, ForeignKey, Column
from sqlmodel import Field, SQLModel
from sqlalchemy.dialects.postgresql import UUID


class PostType(str, Enum):
    BIRTHDAY = "Birthday"
    NOTICE = "Notice"
    BANNER = "Banner"
    JOB_REQUEST = "Job Request"


class PostCategory(str, Enum):
    TEAM = "Team"
    GLOBAL = "Global"


class Posts(SQLModel, table=True):
    __tablename__ = "posts"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True
        )
    )
    type: PostType = Field(default=PostType.NOTICE)
    category: PostCategory = Field(default=PostCategory.GLOBAL)
    caption: Optional[str] = None
    image: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    edited_at: datetime = Field(default_factory=datetime.now)


class Comments(SQLModel, table=True):
    __tablename__ = "comments"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    post_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True),
            ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False
        )
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False
        )
    )
    comment: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)


class Likes(SQLModel, table=True):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "post_id"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    post_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True),
            ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False
        )
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False
        )
    )
    liked_at: datetime = Field(default_factory=datetime.now, nullable=False)
