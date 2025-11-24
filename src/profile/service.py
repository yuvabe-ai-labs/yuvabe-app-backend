from src.notifications.service import get_user_device_tokens
from src.profile.utils import build_raw_message, refresh_access_token
from src.profile.schemas import SendMailRequest
from src.core.models import Assets, Users, UserTeamsRole, Roles
from fastapi import HTTPException
from passlib.context import CryptContext
import httpx
from src.core.config import settings
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime
import uuid
from typing import List
from src.profile.models import (
    Leave,
    UserDevices,
)
from src.profile.notify import send_leave_request_notification

from src.profile.schemas import CreateLeaveRequest, LeaveStatus, ApproveRejectRequest
from src.notifications.fcm import send_fcm


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# src/profile/service.py

# Leave limits (you can move to config)
SICK_LIMIT = getattr(settings, "SICK_LEAVE_LIMIT", 10)
CASUAL_LIMIT = getattr(settings, "CASUAL_LEAVE_LIMIT", 10)


async def _get_team_roles(session: AsyncSession, user_id: uuid.UUID):
    """
    Find user's team, mentor and team lead in that team.
    """
    # 1) Get user's team mapping
    user_team = (
        await session.exec(
            select(UserTeamsRole).where(UserTeamsRole.user_id == user_id)
        )
    ).first()

    if not user_team:
        raise ValueError("User has no team mapping")

    # 2) Get Mentor role
    mentor_role = (
        await session.exec(select(Roles).where(Roles.name == "Mentor"))
    ).first()
    if not mentor_role:
        raise ValueError("Mentor role not found")

    # 3) Get Team Lead role
    lead_role = (
        await session.exec(select(Roles).where(Roles.name == "Team Lead"))
    ).first()
    if not lead_role:
        raise ValueError("Team Lead role not found")

    # 4) Find mentor in same team
    mentor_user = (
        await session.exec(
            select(Users)
            .join(UserTeamsRole, UserTeamsRole.user_id == Users.id)
            .where(UserTeamsRole.team_id == user_team.team_id)
            .where(UserTeamsRole.role_id == mentor_role.id)
        )
    ).first()

    if not mentor_user:
        raise ValueError("Mentor not found in user's team")

    # 5) Find team lead in same team
    lead_user = (
        await session.exec(
            select(Users)
            .join(UserTeamsRole, UserTeamsRole.user_id == Users.id)
            .where(UserTeamsRole.team_id == user_team.team_id)
            .where(UserTeamsRole.role_id == lead_role.id)
        )
    ).first()

    if not lead_user:
        raise ValueError("Team Lead not found in user's team")

    return mentor_user, lead_user


async def _get_tokens_for_users(
    session: AsyncSession, user_ids: List[uuid.UUID]
) -> List[str]:
    """
    Get all device tokens for all given users.
    """
    tokens: List[str] = []
    for uid in user_ids:
        rows = (
            await session.exec(select(UserDevices).where(UserDevices.user_id == uid))
        ).all()
        for row in rows:
            if row.device_token:
                tokens.append(row.device_token)
    return tokens


async def create_leave(session, user_id, body):
    # Get the user
    user = await session.get(Users, user_id)

    # Get mentor + team lead
    mentor_user, lead_user = await _get_team_roles(session, user_id)

    leave = Leave(
        user_id=user_id,
        leave_type=body.leave_type,
        from_date=body.from_date,
        to_date=body.to_date,
        reason=body.reason,
        days=body.days,
        mentor_id=mentor_user.id,
        lead_id=lead_user.id,
    )

    session.add(leave)
    await session.commit()
    await session.refresh(leave)

    # Send notification
    await send_leave_request_notification(
        session,
        user,
        leave,
        leave.mentor_id,
        leave.lead_id,
    )

    return leave


async def mentor_decide_leave(session, mentor_id, leave_id, body):
    leave = await session.get(Leave, leave_id)
    if not leave:
        raise ValueError("Leave not found")

    mentor = await session.get(Users, mentor_id)
    if not mentor:
        raise ValueError("Mentor not found")

    # Update leave status
    leave.status = body.status
    leave.updated_at = datetime.utcnow()

    if body.status == LeaveStatus.REJECTED:
        leave.reject_reason = body.comment

    await session.commit()
    await session.refresh(leave)

    # 🔥 Send notification to USER
    from src.profile.notify import send_leave_status_notification

    await send_leave_status_notification(session, leave, mentor.user_name)

    # 🔥 Send notification to TEAM LEAD also
    tokens = await get_user_device_tokens(session, leave.lead_id)

    await send_fcm(
        tokens,
        "Leave Update",
        f"{leave.user_id} leave was {body.status.lower()}",
        {"type": "leave_status"},
    )

    return leave


# async def apply_leave(session: AsyncSession, user_id, payload: ApplyLeaveRequest):
#     # compute days
#     days = calculate_days(payload.from_date, payload.to_date)
#     if days <= 0:
#         raise HTTPException(status_code=400, detail="Invalid date range")

#     # find mentor and lead
#     mentor, lead = await find_mentor_and_lead(session, user_id)
#     if not mentor or not lead:
#         raise HTTPException(status_code=400, detail="Mentor or Lead not found for user")

#     # check remaining balance
#     limit = SICK_LIMIT if payload.leave_type.lower() == "sick" else CASUAL_LIMIT
#     # sum used days for this leave_type
#     q = select(Leaves).where(
#         Leaves.user_id == user_id,
#         Leaves.leave_type.ilike(payload.leave_type),
#         Leaves.status == "APPROVED",
#     )
#     rows = (await session.exec(q)).all()
#     used = sum(r.days for r in rows) if rows else 0
#     remaining = limit - used
#     if days > remaining:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Insufficient {payload.leave_type} balance. Remaining {remaining}",
#         )

#     leave = Leaves(
#         user_id=user_id,
#         mentor_id=mentor.id,
#         lead_id=lead.id,
#         leave_type=payload.leave_type,
#         from_date=payload.from_date,
#         to_date=payload.to_date,
#         days=days,
#         reason=payload.reason,
#         status="PENDING",
#     )
#     session.add(leave)
#     await session.commit()
#     await session.refresh(leave)

#     # push notifications to mentor & lead
#     title = "New Leave Request"
#     body = f"{user_id} applied {payload.leave_type} leave ({days} days)."
#     mentor_tokens = await get_tokens_for_user(session, mentor.id)
#     lead_tokens = await get_tokens_for_user(session, lead.id)
#     await send_push_to_tokens(
#         mentor_tokens,
#         title,
#         body,
#         data={"leave_id": str(leave.id), "action": "leave_request"},
#     )
#     await send_push_to_tokens(
#         lead_tokens,
#         title,
#         body,
#         data={"leave_id": str(leave.id), "action": "leave_request"},
#     )

#     return leave


# async def get_pending_leaves_for_approver(
#     session: AsyncSession, approver_user_id
# ) -> List[Leaves]:
#     # returns pending leaves where mentor_id == approver OR lead_id == approver
#     stmt = select(Leaves).where(
#         (Leaves.mentor_id == approver_user_id) | (Leaves.lead_id == approver_user_id),
#         Leaves.status == "PENDING",
#     )
#     return (await session.exec(stmt)).all()


# async def get_my_leaves(session: AsyncSession, user_id) -> List[Leaves]:
#     stmt = (
#         select(Leaves)
#         .where(Leaves.user_id == user_id)
#         .order_by(Leaves.created_at.desc())
#     )
#     return (await session.exec(stmt)).all()


# async def get_team_leaves(session: AsyncSession, lead_user_id) -> List[Leaves]:
#     # lead can view leaves where lead_id == lead_user_id
#     stmt = (
#         select(Leaves)
#         .where(Leaves.lead_id == lead_user_id)
#         .order_by(Leaves.created_at.desc())
#     )
#     return (await session.exec(stmt)).all()


# async def approve_leave(
#     session: AsyncSession, approver_id, leave_id: str, comment: Optional[str] = None
# ):
#     # transaction-safe update
#     async with session.begin():
#         stmt = select(Leaves).where(Leaves.id == leave_id).with_for_update()
#         leave = (await session.exec(stmt)).one_or_none()
#         if not leave:
#             raise HTTPException(404, "Leave not found")
#         if leave.status != "PENDING":
#             raise HTTPException(400, "Leave is not pending")

#         # optional: verify approver is mentor or lead for this leave
#         if str(approver_id) not in (str(leave.mentor_id), str(leave.lead_id)):
#             # you might want to check roles more thoroughly
#             raise HTTPException(403, "Not authorized to approve this leave")

#         # check balance again before approving
#         # compute limit and used
#         limit = SICK_LIMIT if leave.leave_type.lower() == "sick" else CASUAL_LIMIT
#         q = select(Leaves).where(
#             Leaves.user_id == leave.user_id,
#             Leaves.leave_type.ilike(leave.leave_type),
#             Leaves.status == "APPROVED",
#         )
#         approved_rows = (await session.exec(q)).all()
#         used = sum(r.days for r in approved_rows) if approved_rows else 0
#         if used + leave.days > limit:
#             raise HTTPException(400, "Insufficient balance at approval time")

#         # update
#         leave.status = "APPROVED"
#         leave.approved_by = approver_id
#         leave.approved_at = datetime.utcnow()
#         if comment:
#             leave.comment = comment

#         session.add(leave)
#     # commit done by context manager

#     # send push notification to member and lead
#     title = "Leave Approved"
#     body = f"Your leave ({leave.leave_type}) has been approved."
#     member_tokens = await get_tokens_for_user(session, leave.user_id)
#     lead_tokens = await get_tokens_for_user(session, leave.lead_id)
#     await send_push_to_tokens(
#         member_tokens,
#         title,
#         body,
#         data={"leave_id": str(leave.id), "action": "leave_approved"},
#     )
#     await send_push_to_tokens(
#         lead_tokens,
#         title,
#         body,
#         data={"leave_id": str(leave.id), "action": "leave_approved"},
#     )

#     return leave


# async def reject_leave(
#     session: AsyncSession,
#     approver_id,
#     leave_id: str,
#     reject_reason: Optional[str] = None,
#     comment: Optional[str] = None,
# ):
#     async with session.begin():
#         stmt = select(Leaves).where(Leaves.id == leave_id).with_for_update()
#         leave = (await session.exec(stmt)).one_or_none()
#         if not leave:
#             raise HTTPException(404, "Leave not found")
#         if leave.status != "PENDING":
#             raise HTTPException(400, "Leave is not pending")

#         if str(approver_id) not in (str(leave.mentor_id), str(leave.lead_id)):
#             raise HTTPException(403, "Not authorized to reject this leave")

#         leave.status = "REJECTED"
#         leave.approved_by = approver_id
#         leave.approved_at = datetime.utcnow()
#         leave.reject_reason = reject_reason
#         if comment:
#             leave.comment = comment
#         session.add(leave)

#     # push to member + lead
#     title = "Leave Rejected"
#     body = f"Your leave ({leave.leave_type}) has been rejected. Reason: {leave.reject_reason or 'N/A'}"
#     member_tokens = await get_tokens_for_user(session, leave.user_id)
#     lead_tokens = await get_tokens_for_user(session, leave.lead_id)
#     await send_push_to_tokens(
#         member_tokens,
#         title,
#         body,
#         data={"leave_id": str(leave.id), "action": "leave_rejected"},
#     )
#     await send_push_to_tokens(
#         lead_tokens,
#         title,
#         body,
#         data={"leave_id": str(leave.id), "action": "leave_rejected"},
#     )

#     return leave


async def add_device_token(session: AsyncSession, user_id, device_token: str):
    """
    Add FCM token to Users.device_tokens ARRAY.
    Avoid duplicates.
    """

    # 1) Fetch user
    user = await session.get(Users, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    # 2) If token not present -> add it
    if device_token not in user.device_tokens:
        user.device_tokens.append(device_token)
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user.device_tokens


# async def get_leave_balance(session: AsyncSession, user_id) -> List[dict]:
#     # compute used for each leave_type and return
#     # using constants SICK_LIMIT and CASUAL_LIMIT
#     stmt = select(Leaves).where(Leaves.user_id == user_id, Leaves.status == "APPROVED")
#     rows = (await session.exec(stmt)).all()
#     used_sick = sum(r.days for r in rows if r.leave_type.lower() == "sick")
#     used_casual = sum(r.days for r in rows if r.leave_type.lower() == "casual")
#     return [
#         {
#             "leave_type": "Sick",
#             "limit": SICK_LIMIT,
#             "used": used_sick,
#             "remaining": max(0, SICK_LIMIT - used_sick),
#         },
#         {
#             "leave_type": "Casual",
#             "limit": CASUAL_LIMIT,
#             "used": used_casual,
#             "remaining": max(0, CASUAL_LIMIT - used_casual),
#         },
#     ]


# In production, replace with DB storage
USER_TOKEN_STORE = {}  # {google_user_id: {tokens}}


async def send_email_service(req: SendMailRequest):
    record = USER_TOKEN_STORE.get(req.user_id)
    if not record:
        raise HTTPException(404, "User not logged in with Google OAuth")

    access_token = record["access_token"]
    refresh_token = record.get("refresh_token")

    if not access_token and refresh_token:
        new_tokens = await refresh_access_token(refresh_token)
        access_token = new_tokens["access_token"]
        record["access_token"] = access_token

    if not access_token:
        raise HTTPException(400, "Re-auth required")

    raw = build_raw_message(
        to_email=req.to,
        subject=req.subject,
        body=req.body,
        from_name=req.from_name,
        from_email=record["email"],
    )

    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    payload = {"raw": raw}

    async with httpx.AsyncClient() as client:
        r = await client.post(
            url, json=payload, headers={"Authorization": f"Bearer {access_token}"}
        )

    if r.status_code >= 400:
        raise HTTPException(500, f"Gmail error: {r.text}")

    return r.json()


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
    q = await session.exec(select(Assets).where(Assets.user_id == uuid.UUID(user_id)))
    return q.all()
