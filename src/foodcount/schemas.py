from datetime import date
from pydantic import BaseModel


class LunchNotifyRequest(BaseModel):
    start_date: date
    end_date: date


class LunchNotifyResponse(BaseModel):
    status: str
    sent_to: str
