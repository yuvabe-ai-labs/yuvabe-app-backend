from datetime import date, timedelta

from sqlmodel import Session, select

from src.core.models import EmotionLogs, Users

from .schemas import EmotionLogCreate, EmotionLogResponse, HomeResponse

PHILOSOPHY_TEXT = "Your mind is your greatest asset — train it daily."


def get_home_data(user_id: str, session: Session) -> HomeResponse:
    # Fetch user info
    user = session.exec(select(Users).where(Users.id == user_id)).first()
    if not user:
        raise ValueError("User not found")

    # Fetch last 7 days of emotion logs
    seven_days_ago = date.today() - timedelta(days=7)
    emotion_logs = session.exec(
        select(EmotionLogs)
        .where(EmotionLogs.user_id == user_id)
        .where(EmotionLogs.log_date >= seven_days_ago)
        .order_by(EmotionLogs.log_date)
    ).all()

    emotion_responses = [
        EmotionLogResponse(
            log_date=log.log_date,
            morning_emotion=log.morning_emotion,
            evening_emotion=log.evening_emotion,
        )
        for log in emotion_logs
    ]

    return HomeResponse(
        user_id=str(user.id),
        user_name=user.user_name,
        philosophy_text=PHILOSOPHY_TEXT,
        recent_emotions=emotion_responses,
    )


def add_or_update_emotion(data: EmotionLogCreate, session: Session):
    existing_log = session.exec(
        select(EmotionLogs)
        .where(EmotionLogs.user_id == data.user_id)
        .where(EmotionLogs.log_date == data.log_date)
    ).first()

    if existing_log:
        # Update existing record
        if data.morning_emotion is not None:
            existing_log.morning_emotion = data.morning_emotion
        if data.evening_emotion is not None:
            existing_log.evening_emotion = data.evening_emotion
    else:
        new_log = EmotionLogs(
            user_id=data.user_id,
            morning_emotion=data.morning_emotion,
            evening_emotion=data.evening_emotion,
            log_date=data.log_date,
        )
        session.add(new_log)

    session.commit()
    session.refresh(existing_log or new_log)
    return existing_log or new_log


def get_emotions(user_id: str, session: Session):
    logs = session.exec(
        select(EmotionLogs)
        .where(EmotionLogs.user_id == user_id)
        .order_by(EmotionLogs.log_date.desc())
    ).all()

    return [
        EmotionLogResponse(
            log_date=log.log_date,
            morning_emotion=log.morning_emotion,
            evening_emotion=log.evening_emotion,
        )
        for log in logs
    ]
