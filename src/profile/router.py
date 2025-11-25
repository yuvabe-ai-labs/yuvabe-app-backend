from src.core.database import get_async_session
from src.auth.utils import get_current_user
from src.profile.models import Leave, LeaveType, LeaveStatus
from src.auth.schemas import BaseResponse
from sqlalchemy import desc
from sqlalchemy.ext.asyncio.session import AsyncSession
from fastapi.params import Depends
from src.core.models import Users, Teams, Roles, UserTeamsRole
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.utils import get_current_user  # adjust path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import uuid
from src.core.models import Users
from src.profile.schemas import (
    CreateLeaveRequest,
    LeaveResponse,
    ApproveRejectRequest,
    LeaveStatus,
)
from src.profile.service import create_leave, mentor_decide_leave


router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("/request", response_model=LeaveResponse)
async def request_leave_route(
    body: CreateLeaveRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    # convert user_id string -> UUID if needed
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user id format")

    leave = await create_leave(session, user_uuid, body)

    return LeaveResponse(
        id=str(leave.id),
        leave_type=leave.leave_type,
        from_date=leave.from_date,
        to_date=leave.to_date,
        days=leave.days,
        reason=leave.reason,
        status=leave.status,
        mentor_id=str(leave.mentor_id),
        lead_id=str(leave.lead_id),
    )


@router.post("/{leave_id}/mentor-decision", response_model=LeaveResponse)
async def mentor_decision_route(
    leave_id: str,
    body: ApproveRejectRequest,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    # validate leave_id + user_id UUIDs
    try:
        leave_uuid = uuid.UUID(leave_id)
        mentor_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    # If rejected, comment must be provided
    if body.status == LeaveStatus.REJECTED and not body.comment:
        raise HTTPException(
            status_code=400,
            detail="Comment is required when rejecting leave",
        )



    try:
        leave = await mentor_decide_leave(session, mentor_uuid, leave_uuid, body)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return LeaveResponse(
        id=str(leave.id),
        leave_type=leave.leave_type,
        from_date=leave.from_date,
        to_date=leave.to_date,
        days=leave.days,
        reason=leave.reason,
        status=leave.status,
        mentor_id=str(leave.mentor_id),
        lead_id=str(leave.lead_id),
    )


SICK_LIMIT = 10
CASUAL_LIMIT = 10


@router.get("/balance")
async def get_leave_balance(
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    stmt = select(Leave).where(
        Leave.user_id == user_id, Leave.status == LeaveStatus.APPROVED
    )
    results = (await session.exec(stmt)).all()

    sick_used = sum(1 for l in results if l.leave_type == LeaveType.SICK)
    casual_used = sum(1 for l in results if l.leave_type == LeaveType.CASUAL)

    sick_remaining = SICK_LIMIT - sick_used
    casual_remaining = CASUAL_LIMIT - casual_used

    return {
        "code": 200,
        "message": "success",
        "data": {
            "sick_remaining": sick_remaining,
            "casual_remaining": casual_remaining,
        },
    }


@router.get("/balance/{user_id}")
async def get_leave_balance_for_user(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Leave).where(
        Leave.user_id == user_id, Leave.status == LeaveStatus.APPROVED
    )
    results = (await session.exec(stmt)).all()

    sick_used = sum(1 for l in results if l.leave_type == LeaveType.SICK)
    casual_used = sum(1 for l in results if l.leave_type == LeaveType.CASUAL)

    sick_remaining = SICK_LIMIT - sick_used
    casual_remaining = CASUAL_LIMIT - casual_used

    return {
        "code": 200,
        "message": "success",
        "data": {
            "sick_remaining": sick_remaining,
            "casual_remaining": casual_remaining,
        },
    }


@router.get("/notifications")
async def list_notifications(
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    from src.profile.models import Leave

    stmt = (
        select(Leave)
        .where(
            (Leave.user_id == user_id)
            | (Leave.mentor_id == user_id)
            | (Leave.lead_id == user_id)
        )
        .order_by(desc(Leave.updated_at))
    )

    results = (await session.exec(stmt)).all()

    notifications = []

    for leave in results:
        if leave.user_id == user_id:
            # user = leave owner
            title = f"Your leave was {leave.status}"
            body = f"{leave.leave_type} from {leave.from_date} to {leave.to_date}"
        elif leave.mentor_id == user_id:
            # mentor receives new leave request
            title = "New Leave Request"
            body = f"{leave.leave_type} requested by user"
        elif leave.lead_id == user_id:
            # lead receives updates
            title = f"Leave {leave.status}"
            body = f"{leave.leave_type} for user updated"
        else:
            title = "Leave Update"
            body = leave.reason or ""

        notifications.append(
            {
                "id": str(leave.id),
                "mentor_id": str(leave.mentor_id),
                "lead_id": str(leave.lead_id),
                "title": title,
                "body": body,
                "type": leave.status,
                "updated_at": leave.updated_at.isoformat(),
                "leave_type": leave.leave_type,
                "from_date": str(leave.from_date),
                "to_date": str(leave.to_date),
                "reject_reason": leave.reject_reason,
                "reason": leave.reason,
            }
        )

    return {"code": 200, "data": notifications}


@router.get("/leave/{leave_id}")
async def get_leave_details(
    leave_id: str,
    session: AsyncSession = Depends(get_async_session),
    user_id: str = Depends(get_current_user),
):
    leave = await session.get(Leave, leave_id)

    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")

    # Convert to JSON response
    return {
        "code": 200,
        "data": {
            "id": str(leave.id),
            "user_id": str(leave.user_id),
            "mentor_id": str(leave.mentor_id),
            "lead_id": str(leave.lead_id),
            "leave_type": leave.leave_type,
            "from_date": str(leave.from_date),
            "to_date": str(leave.to_date),
            "days": leave.days,
            "reason": leave.reason,
            "status": leave.status,
            "reject_reason": leave.reject_reason,
            "updated_at": leave.updated_at.isoformat(),
        },
    }


@router.get("/mentor/pending")
async def mentor_pending_leaves(
    session: AsyncSession = Depends(get_async_session),
    mentor_id: str = Depends(get_current_user),
):
    stmt = select(Leave).where(
        Leave.mentor_id == mentor_id,
        Leave.status == LeaveStatus.PENDING,
    )

    rows = (await session.exec(stmt)).all()

    return {
        "code": 200,
        "data": [
            LeaveResponse(
                id=str(r.id),
                leave_type=r.leave_type,
                from_date=r.from_date,
                to_date=r.to_date,
                days=r.days,
                reason=r.reason,
                status=r.status,
                mentor_id=str(r.mentor_id),
                lead_id=str(r.lead_id),
            )
            for r in rows
        ],
    }


@router.get("/contacts", response_model=BaseResponse)
async def get_leave_contacts(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    # get_current_user returns a STRING user_id
    user_id = current_user

    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user token")

    # 1) Get user's team
    stmt = select(UserTeamsRole).where(UserTeamsRole.user_id == user_id)
    ut = (await session.exec(stmt)).first()

    if not ut:
        raise HTTPException(status_code=404, detail="User-Team mapping not found")

    # 2) Get Team Lead role
    lead_role = (
        await session.exec(select(Roles).where(Roles.name == "Team Lead"))
    ).first()

    if not lead_role:
        raise HTTPException(status_code=500, detail="Team Lead role not found")

    # 3) Find Team Lead user in same team
    lead_user = (
        await session.exec(
            select(Users)
            .join(UserTeamsRole)
            .where(UserTeamsRole.team_id == ut.team_id)
            .where(UserTeamsRole.role_id == lead_role.id)
        )
    ).all()

    if not lead_user:
        raise HTTPException(status_code=404, detail="Team lead not found")

    to_email = ", ".join([u.email_id for u in lead_user])

    # 4) HR CC emails
    hr_team = (await session.exec(select(Teams).where(Teams.name == "HR Team"))).first()

    cc = []
    if hr_team:
        hr_users = (
            await session.exec(
                select(Users)
                .join(UserTeamsRole)
                .where(UserTeamsRole.team_id == hr_team.id)
            )
        ).all()

        cc = [str(row.email_id) for row in hr_users]

    return BaseResponse(code=200, message="success", data={"to": to_email, "cc": cc})


@router.get("/details", response_model=BaseResponse)
async def get_profile_details(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    user_id = current_user

    # 1) Get the user
    user = await session.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Get user's team mapping
    user_team = (
        await session.exec(
            select(UserTeamsRole).where(UserTeamsRole.user_id == user_id)
        )
    ).first()

    if not user_team:
        raise HTTPException(status_code=404, detail="User does not belong to any team")

    # 3) Get team name
    team = await session.get(Teams, user_team.team_id)

    # 4) Find mentor (team lead)
    lead_role = (
        await session.exec(select(Roles).where(Roles.name == "Mentor"))
    ).first()

    mentor_users = (
        await session.exec(
            select(Users)
            .join(UserTeamsRole)
            .where(UserTeamsRole.team_id == user_team.team_id)
            .where(UserTeamsRole.role_id == lead_role.id)
        )
    ).all()

    mentor_names = [u.user_name for u in mentor_users]
    mentor_emails = [u.email_id for u in mentor_users]

    return BaseResponse(
        code=200,
        message="success",
        data={
            "name": user.user_name,
            "email": user.email_id,
            "team_name": team.name,
            "mentor_name": ", ".join(mentor_names),
            "mentor_email": ", ".join(mentor_emails),
        },
    )
