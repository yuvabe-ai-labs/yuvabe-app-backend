from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from src.core.enums import Emotion

class EmotionLogCreate(BaseModel):
    user_id: str
    morning_emotion: Optional[Emotion] = None
    evening_emotion: Optional[Emotion] = None
    log_date: date


class EmotionLogResponse(BaseModel):
    log_date: date
    morning_emotion: Optional[Emotion]
    evening_emotion: Optional[Emotion]


class HomeResponseData(BaseModel):
    user_id: str
    user_name: str
    philosophy_text: str
    recent_emotions: List[EmotionLogResponse]


class BroadcastNotificationRequest(BaseModel):
    title: str
    body: str
    data: dict | None = None
