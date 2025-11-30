from src.core.database import get_async_session
from src.auth.utils import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import List
from src.wellbeing.schemas import WaterLogCreate, WaterLogUpdate, WaterLog
from . import service
from sqlalchemy.ext.asyncio.session import AsyncSession

router = APIRouter(prefix="/wellbeing", tags=["Wellbeing"])


# Create a new water log
@router.post("/water_logs/", response_model=WaterLog)
async def create_water_log(
    water_log: WaterLogCreate,
    session: AsyncSession = Depends(get_async_session),
    user_id: UUID = Depends(get_current_user),
):
    return await service.create_water_log(session, water_log, user_id)


# Get all water logs for a user
@router.get("/water_logs/", response_model=List[WaterLog])
async def get_water_logs(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
    user_id: UUID = Depends(get_current_user),
):
    return await service.get_water_logs(session, user_id, skip=skip, limit=limit)


# Update a water log
@router.put("/water_logs/{water_log_id}", response_model=WaterLog)
async def update_water_log(
    water_log_id: UUID,
    water_log: WaterLogUpdate,
    session: AsyncSession = Depends(get_async_session),
    user_id: UUID = Depends(get_current_user),
):
    updated_log = service.update_water_log(session, water_log_id, water_log)
    if not updated_log:
        raise HTTPException(status_code=404, detail="Water log not found")
    return await updated_log


# Delete a water log
@router.delete("/water_logs/{water_log_id}")
async def delete_water_log(
    water_log_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    user_id: UUID = Depends(get_current_user),
):
    success = service.delete_water_log(session, water_log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Water log not found")
    return {"message": "Water log deleted successfully"}
