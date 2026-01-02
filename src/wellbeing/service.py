from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List , Dict
from .models import WaterLogs
import uuid
from .schemas import WaterLogCreate, WaterLogUpdate, StepsLogCreate
from datetime import date, datetime , timedelta



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
        existing_log.logged_at = datetime.utcnow()
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
        db_water_log.logged_at = datetime.utcnow()
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


async def create_or_update_steps(
    session: AsyncSession,
    steps: StepsLogCreate,
    user_id: uuid.UUID,
) -> WaterLogs:

    today = date.today()

    stmt = select(WaterLogs).filter(
        WaterLogs.user_id == user_id,
        WaterLogs.logged_at >= datetime.combine(today, datetime.min.time()),
        WaterLogs.logged_at <= datetime.combine(today, datetime.max.time()),
    )

    result = await session.execute(stmt)
    existing_log = result.scalar_one_or_none()

    # UPDATE existing row
    if existing_log:
        existing_log.steps_count = steps.steps_count  # overwrite
        existing_log.logged_at = datetime.utcnow()
        await session.commit()
        await session.refresh(existing_log)
        return existing_log

    # CREATE new row
    new_log = WaterLogs(
        id=uuid.uuid4(),
        user_id=user_id,
        steps_count=steps.steps_count,
        logged_at=datetime.utcnow(),
    )

    session.add(new_log)
    await session.commit()
    await session.refresh(new_log)
    return new_log

async def get_steps_logs(
    session: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 30,
) -> List[WaterLogs]:
    """
    Get step logs for a user (latest first)
    """

    stmt = (
        select(WaterLogs)
        .filter(
            WaterLogs.user_id == user_id,
            WaterLogs.steps_count.isnot(None),
        )
        .order_by(WaterLogs.logged_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await session.execute(stmt)
    return result.scalars().all()






async def get_weekly_steps(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> Dict[str, int]:
    """
    Returns steps grouped by weekday for current week
    Example:
    {
      "Mon": 3200,
      "Tue": 4500,
      ...
    }
    """

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)

    stmt = select(WaterLogs).filter(
        WaterLogs.user_id == user_id,
        WaterLogs.steps_count.isnot(None),
        WaterLogs.logged_at >= start_of_week,
        WaterLogs.logged_at <= end_of_week,
    )

    result = await session.execute(stmt)
    logs = result.scalars().all()

    week_map = {
        "Mon": 0,
        "Tue": 0,
        "Wed": 0,
        "Thu": 0,
        "Fri": 0,
        "Sat": 0,
        "Sun": 0,
    }

    for log in logs:
        day = log.logged_at.strftime("%a")
        week_map[day] = log.steps_count

    return week_map
