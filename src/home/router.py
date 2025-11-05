from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from src.core.database import engine

from .schemas import EmotionLogCreate, EmotionLogResponse, HomeResponse
from .service import add_or_update_emotion, get_emotions, get_home_data

router = APIRouter(prefix="/home", tags=["Home"])


def get_session():
    with Session(engine) as session:
        yield session


@router.get("/{user_id}", response_model=HomeResponse)
def fetch_home_data(user_id: str, session: Session = Depends(get_session)):
    try:
        return get_home_data(user_id, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/emotion", response_model=EmotionLogResponse)
def create_or_update_emotion(
    data: EmotionLogCreate, session: Session = Depends(get_session)
):
    record = add_or_update_emotion(data, session)
    return EmotionLogResponse(
        log_date=record.log_date,
        morning_emotion=record.morning_emotion,
        evening_emotion=record.evening_emotion,
    )


@router.get("/emotion/{user_id}", response_model=list[EmotionLogResponse])
def get_user_emotions(user_id: str, session: Session = Depends(get_session)):
    return get_emotions(user_id, session)
