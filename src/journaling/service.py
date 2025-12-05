from datetime import datetime
import uuid
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.models import Users
from src.journaling.models import JournalEntry
from src.journaling.schemas import JournalCreate, JournalUpdate


async def create_or_update_journal(data: JournalCreate, session: AsyncSession):
    user = await session.exec(select(Users).where(Users.id == data.user_id))
    if not user.first():
        raise ValueError("User not found")

    query = select(JournalEntry).where(
        JournalEntry.user_id == data.user_id,
        JournalEntry.journal_date == data.journal_date
    )
    existing = (await session.exec(query)).first()

    if existing:
        existing.title = data.title
        existing.content = data.content
        existing.updated_at = datetime.utcnow()
        record = existing
    else:
        record = JournalEntry(
            user_id=data.user_id,
            title=data.title,
            content=data.content,
            journal_date=data.journal_date,
        )
        session.add(record)

    await session.commit()
    await session.refresh(record)
    return record


async def get_all_journals(user_id: uuid.UUID, session: AsyncSession):
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.user_id == user_id)
        .order_by(JournalEntry.journal_date.desc())
    )
    result = await session.exec(stmt)
    return result.all()


async def get_journal(journal_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession):
    stmt = select(JournalEntry).where(JournalEntry.id == journal_id)
    result = await session.exec(stmt)
    record = result.first()

    if not record:
        raise ValueError("Journal entry not found")
    if str(record.user_id) != user_id:
        raise ValueError("Not authorized")

    return record


async def update_journal(
    journal_id: uuid.UUID,
    data: JournalUpdate,
    user_id: uuid.UUID,
    session: AsyncSession,
):
    record = await get_journal(journal_id, user_id, session)

    if data.title is not None:
        record.title = data.title

    if data.content is not None:
        record.content = data.content

    if data.journal_date is not None:
        record.journal_date = data.journal_date

    record.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(record)
    return record


async def delete_journal(journal_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession):
    record = await get_journal(journal_id, user_id, session)
    await session.delete(record)
    await session.commit()
