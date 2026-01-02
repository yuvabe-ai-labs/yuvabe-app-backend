from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime


class WaterLogBase(BaseModel):

    amount_ml: Optional[int] = None

    goal_ml: Optional[int] = None
    recommended_ml: Optional[int] = None


class WaterLogCreate(WaterLogBase):
    pass


class WaterLogUpdate(WaterLogBase):
    pass


class WaterLog(WaterLogBase):
    id: uuid.UUID
    user_id: uuid.UUID
    logged_at: datetime

    model_config = {"from_attributes": True}


class StepsLogBase(BaseModel):
    steps_count: int


class StepsLogCreate(StepsLogBase):
    pass


class StepsLog(StepsLogBase):
    id: uuid.UUID
    user_id: uuid.UUID
    logged_at: datetime

    model_config = {"from_attributes": True}
