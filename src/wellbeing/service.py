from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from .models import WaterLogs
import uuid
from .schemas import WaterLogCreate, WaterLogUpdate
from datetime import date, datetime


# Create or update today's water log
async def create_water_log(
    session: AsyncSession, water_log: WaterLogCreate, user_id: uuid.UUID
) -> WaterLogs:
    

    today = date.today()

    # 1️⃣ Query today's existing log
    stmt = select(WaterLogs).filter(
        WaterLogs.user_id == user_id,
        WaterLogs.logged_at >= datetime.combine(today, datetime.min.time()),
        WaterLogs.logged_at <= datetime.combine(today, datetime.max.time()),
    )
    result = await session.execute(stmt)
    existing_log = result.scalar_one_or_none()

    # 2️⃣ If today's log exists → UPDATE it
    if existing_log:
        existing_log.amount_ml = water_log.amount_ml
        existing_log.goal_ml = water_log.goal_ml
        existing_log.recommended_ml = water_log.recommended_ml
        await session.commit()
        await session.refresh(existing_log)
        return existing_log

    # 3️⃣ No log for today → CREATE a new one
    new_log = WaterLogs(
        id=uuid.uuid4(),
        user_id=user_id,
        amount_ml=water_log.amount_ml,
        logged_at=datetime.utcnow(),
        goal_ml=water_log.goal_ml,
        recommended_ml=water_log.recommended_ml,
    )
    session.add(new_log)
    await session.commit()
    await session.refresh(new_log)
    return new_log


# Get all water logs for a user
async def get_water_logs(
    session: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[WaterLogs]:
    stmt = (
        select(WaterLogs).filter(WaterLogs.user_id == user_id).offset(skip).limit(limit)
    )
    result = await session.execute(stmt)  # Execute asynchronously
    return result.scalars().all()  # Fetch results asynchronously


# Update a water log
async def update_water_log(
    session: AsyncSession, water_log_id: uuid.UUID, water_log: WaterLogUpdate
) -> WaterLogs:
    stmt = select(WaterLogs).filter(WaterLogs.id == water_log_id)
    result = await session.execute(stmt)  # Execute asynchronously
    db_water_log = result.scalar_one_or_none()

    if db_water_log:
        db_water_log.amount_ml = water_log.amount_ml
        db_water_log.goal_ml = water_log.goal_ml
        db_water_log.recommended_ml = water_log.recommended_ml
        await session.commit()  # Commit asynchronously
        await session.refresh(db_water_log)  # Refresh asynchronously
        return db_water_log
    return None


# Delete a water log
async def delete_water_log(session: AsyncSession, water_log_id: uuid.UUID) -> bool:
    stmt = select(WaterLogs).filter(WaterLogs.id == water_log_id)
    result = await session.execute(stmt)  # Execute asynchronously
    db_water_log = result.scalar_one_or_none()

    if db_water_log:
        await session.delete(db_water_log)  # Delete asynchronously
        await session.commit()  # Commit asynchronously
        return True
    return False
