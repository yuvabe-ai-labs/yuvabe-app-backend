import uuid
from datetime import datetime
from typing import List

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel


class KnowledgeBase(SQLModel, table=True):
    __tablename__ = "knowledge_base"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False)
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    knowledge_chunk: List["KnowledgeChunk"] = Relationship(
        back_populates="knowledge_base"
    )


class KnowledgeChunk(SQLModel, table=True):
    __tablename__ = "knowledge_chunk"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    kb_id: uuid.UUID = Field(foreign_key="knowledge_base.id", nullable=False)
    chunk_index: int
    chunk_text: str
    embedding: List[float] = Field(sa_column=Column(Vector(768)))
    knowledge_base: "KnowledgeBase" = Relationship(back_populates="knowledge_chunk")
