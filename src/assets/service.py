import uuid
from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.models import Assets

async def list_user_assets(session: AsyncSession, user_id: str) -> List[Assets]:
    q = await session.exec(
        select(Assets).where(Assets.user_id == uuid.UUID(user_id))
    )
    return q.all()
