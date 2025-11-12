from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.database import get_async_session
from src.core.schemas import BaseResponse

from .schemas import EmotionLogCreate, EmotionLogResponse, HomeResponseData
from .service import add_or_update_emotion, get_emotions, get_home_data

router = APIRouter(prefix="/home", tags=["Home"])


@router.get("/{user_id}", response_model=BaseResponse[HomeResponseData])
async def fetch_home_data(
    user_id: str, session: AsyncSession = Depends(get_async_session)
):
    try:
        data = await get_home_data(user_id, session)
        return {"status_code": 200, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/emotion", response_model=BaseResponse[EmotionLogResponse])
async def create_or_update_emotion(
    data: EmotionLogCreate, session: AsyncSession = Depends(get_async_session)
):
    record = await add_or_update_emotion(data, session)
    return {
        "status_code": 200,
        "data": record,
    }


@router.get("/emotion/{user_id}", response_model=BaseResponse[List[EmotionLogResponse]])
async def get_user_emotions(
    user_id: str, session: AsyncSession = Depends(get_async_session)
):
    data = await get_emotions(user_id, session)
    return {"status_code": 200, "data": data}
