from src.notifications.service import get_user_device_tokens
from src.notifications.fcm import send_fcm


# -------------------------------
# SEND TO MENTOR + LEAD
# -------------------------------
async def send_leave_request_notification(session, user, leave, mentor_id, lead_id):
    title = "New Leave Request"
    body = f"{user.user_name} requested leave"

    tokens = []
    tokens += await get_user_device_tokens(session, mentor_id)
    tokens += await get_user_device_tokens(session, lead_id)

    await send_fcm(
        tokens,
        title,
        body,
        {
            "type": "leave_request",
            "screen": "MentorApproval",
            "leave_id": str(leave.id),
        },
    )


# -------------------------------
# SEND TO USER + TEAM LEAD
# -------------------------------
async def send_leave_status_notification(session, leave, mentor_name):
    title = f"Leave {leave.status}"
    body = f"Your leave was {leave.status.lower()} by {mentor_name}"

    # Send to USER
    tokens = await get_user_device_tokens(session, leave.user_id)
    await send_fcm(
        tokens,
        title,
        body,
        {
            "type": "leave_status",
            "screen": "LeaveDetails",
            "leave_id": str(leave.id),
        },
    )

    # Send to TEAM LEAD
    tokens = await get_user_device_tokens(session, leave.lead_id)
    await send_fcm(
        tokens,
        title,
        f"Leave {leave.status} for user {leave.user_id}",
        {
            "type": "lead_update",
            "screen": "LeaveDetails",
            "leave_id": str(leave.id),
        },
    )
