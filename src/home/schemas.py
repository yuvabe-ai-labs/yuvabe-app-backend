# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument

from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class EmotionLogCreate(BaseModel):
    user_id: str
    morning_emotion: Optional[int] = None
    evening_emotion: Optional[int] = None
    log_date: date


class EmotionLogResponse(BaseModel):
    log_date: date
    morning_emotion: Optional[int]
    eveing_emotion: Optional[int]


class HomeResponse(BaseModel):
    user_id: str
    user_name: str
    philosophy_text: str
    recent_emotions: List[EmotionLogResponse]
