import uuid
from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel


class JournalBase(SQLModel):
    title: str
    content: str
    journal_date: date


class JournalCreate(JournalBase):
    user_id: Optional[uuid.UUID] = None 


class JournalUpdate(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    journal_date: Optional[date] = None


class JournalResponse(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    content: str
    journal_date: date
    created_at: datetime
    updated_at: datetime
