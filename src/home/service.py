from datetime import date, timedelta

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.models import EmotionLogs, Users
from src.profile.models import UserDevices
from src.notifications.fcm import send_fcm
from .schemas import EmotionLogCreate, EmotionLogResponse, HomeResponseData

PHILOSOPHY_TEXT = "Your mind is your greatest asset — train it daily."


async def get_home_data(user_id: str, session: AsyncSession) -> HomeResponseData:
    result = await session.exec(select(Users).where(Users.id == user_id))
    user = result.first()
    if not user:
        raise ValueError("User not found")

    seven_days_ago = date.today() - timedelta(days=7)
    result = await session.exec(
        select(EmotionLogs)
        .where(EmotionLogs.user_id == user_id)
        .where(EmotionLogs.log_date >= seven_days_ago)
        .order_by(EmotionLogs.log_date)
    )
    emotion_logs = result.all()

    emotion_responses = [
        EmotionLogResponse(
            log_date=log.log_date,
            morning_emotion=log.morning_emotion,
            evening_emotion=log.evening_emotion,
        )
        for log in emotion_logs
    ]

    return HomeResponseData(
        user_id=str(user.id),
        user_name=user.user_name,
        philosophy_text=PHILOSOPHY_TEXT,
        recent_emotions=emotion_responses,
    )


async def add_or_update_emotion(
    data: EmotionLogCreate, session: AsyncSession
) -> EmotionLogResponse:

    user_exists = await session.exec(select(Users).where(Users.id == data.user_id))
    if not user_exists.first():
        raise ValueError("User not found. Cannot add emotion log.")

    result = await session.exec(
        select(EmotionLogs)
        .where(EmotionLogs.user_id == data.user_id)
        .where(EmotionLogs.log_date == data.log_date)
    )
    existing_log = result.first()

    if existing_log:
        if data.morning_emotion is not None:
            existing_log.morning_emotion = data.morning_emotion
        if data.evening_emotion is not None:
            existing_log.evening_emotion = data.evening_emotion
        record = existing_log
    else:
        record = EmotionLogs(
            user_id=data.user_id,
            morning_emotion=data.morning_emotion,
            evening_emotion=data.evening_emotion,
            log_date=data.log_date,
        )
        session.add(record)

    await session.commit()
    await session.refresh(record)

    return EmotionLogResponse(
        log_date=record.log_date,
        morning_emotion=record.morning_emotion,
        evening_emotion=record.evening_emotion,
    )


async def get_emotions(user_id: str, session: AsyncSession):
    result = await session.exec(
        select(EmotionLogs)
        .where(EmotionLogs.user_id == user_id)
        .order_by(EmotionLogs.log_date.desc())
    )
    logs = result.all()

    return [
        EmotionLogResponse(
            log_date=log.log_date,
            morning_emotion=log.morning_emotion,
            evening_emotion=log.evening_emotion,
        )
        for log in logs
    ]

async def get_all_device_tokens(session):
    stmt = select(UserDevices.device_token)
    rows = (await session.execute(stmt)).all()
    return [r[0] for r in rows]


async def send_broadcast_notification(session, title, body, data=None):
    tokens = await get_all_device_tokens(session)

    if not tokens:
        return {"sent": 0}

    await send_fcm(tokens, title, body, data)
    return {"sent": len(tokens)}