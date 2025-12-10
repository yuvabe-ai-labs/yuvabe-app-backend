from src.notifications.service import get_user_device_tokens
from src.notifications.fcm import send_fcm


def ensure_list(value):
    """
    Makes sure the value is always a list.
    - If it's already a list/tuple/set -> convert to list and return
    - If it's None -> return empty list
    - Otherwise -> wrap single value in a list
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


# -------------------------------
# SEND TO MENTOR + LEAD
# -------------------------------
# -------------------------------
# SEND TO MENTOR + LEAD
# -------------------------------
async def send_leave_request_notification(session, user, leave, mentor_ids, lead_ids):
    mentor_ids = ensure_list(mentor_ids)
    lead_ids = ensure_list(lead_ids)

    # ---------------------------
    # SEND TO MENTORS (Approval screen)
    # ---------------------------
    mentor_tokens = []
    for mentor_id in mentor_ids:
        mentor_tokens += await get_user_device_tokens(session, mentor_id)

    mentor_tokens = list(set(mentor_tokens))

    if mentor_tokens:
        await send_fcm(
            mentor_tokens,
            "New Leave Request",
            f"{user.user_name} requested leave",
            {
                "type": "leave_request",
                "screen": "MentorApproval", 
                "leave_id": str(leave.id),
            },
            priority="high",
        )

    # ---------------------------
    # SEND TO TEAM LEADS (Leave Details screen)
    # ---------------------------
    lead_tokens = []
    for lead_id in lead_ids:
        lead_tokens += await get_user_device_tokens(session, lead_id)

    lead_tokens = list(set(lead_tokens))

    if lead_tokens:
        await send_fcm(
            lead_tokens,
            "New Leave Request",
            f"{user.user_name} requested leave",
            {
                "type": "leave_request",
                "screen": "LeaveDetails",  
                "leave_id": str(leave.id),
            },
            priority="high",
        )


# -------------------------------
# SEND TO USER + TEAM LEAD
# -------------------------------
async def send_leave_status_notification(session, leave, mentor_name, lead_ids):
    title = f"Leave {leave.status}"
    body = f"Your leave was {leave.status.lower()} by {mentor_name}"

    # Send to USER
    user_tokens = await get_user_device_tokens(session, leave.user_id)

    # Send to TEAM LEADS
    lead_tokens = []
    for lead_id in lead_ids:
        lead_tokens += await get_user_device_tokens(session, lead_id)

    lead_tokens = list(set(lead_tokens))

    # 1) Notify user
    await send_fcm(
        user_tokens,
        title,
        body,
        {
            "type": "leave_status",
            "screen": "LeaveDetails",
            "leave_id": str(leave.id),
        },
        priority="high",
    )

    # 2) Notify all leads
    await send_fcm(
        lead_tokens,
        title,
        f"Leave {leave.status} for user {leave.user_id}",
        {
            "type": "lead_update",
            "screen": "LeaveDetails",
            "leave_id": str(leave.id),
        },
        priority="high",
    )
