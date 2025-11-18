from src.core.models import Assets
from ast import List
from datetime import datetime
import uuid
from fastapi import HTTPException
from passlib.context import CryptContext
from src.core.models import Users
import uuid
from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.models import Assets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def update_user_profile(session, user_id: str, data):
    user = await session.get(Users, uuid.UUID(user_id))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # --- Update Name ---
    if data.name:
        user.user_name = data.name

    # --- Update Email ---
    if data.email:
        user.email_id = data.email

    # --- Update DOB ---
    if data.dob:
        try:
            # Convert DD.MM.YYYY → Python date
            parsed_date = datetime.strptime(data.dob, "%d.%m.%Y").date()
            user.dob = parsed_date
        except:
            raise HTTPException(
                status_code=400, detail="DOB must be in DD.MM.YYYY format"
            )

    # --- Update Address ---
    if data.address:
        user.address = data.address

    # --- Change Password ---
    if data.new_password:
        if not data.current_password:
            raise HTTPException(status_code=400, detail="Current password required")

        # Verify old password
        if not pwd_context.verify(data.current_password, user.password):
            raise HTTPException(status_code=400, detail="Incorrect current password")

        # Set new password
        user.password = pwd_context.hash(data.new_password)

    # Commit changes
    await session.commit()
    await session.refresh(user)

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": str(user.id),
            "name": user.user_name,
            "email": user.email_id,
            "dob": user.dob.isoformat() if user.dob else None,
            "address": user.address,
            "is_verified": user.is_verified,
        },
    }

async def list_user_assets(session: AsyncSession, user_id: str) -> List[Assets]:
    q = await session.exec(
        select(Assets).where(Assets.user_id == uuid.UUID(user_id))
    )
    return q.all()