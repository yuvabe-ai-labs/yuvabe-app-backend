import os
import json
import httpx
from google.oauth2 import service_account
import google.auth.transport.requests

# Your Firebase project ID (from project settings)
FCM_PROJECT_ID = "yuvabe-478505"  # <-- change this

# Path to your service account file
SERVICE_ACCOUNT_FILE = os.path.join(
    os.path.dirname(__file__), "yuvabe-478505-09433c5e6e33.json"
)


def get_access_token():
    """Generate OAuth2 access token for FCM HTTP v1."""
    scopes = ["https://www.googleapis.com/auth/firebase.messaging"]

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scopes
    )

    request = google.auth.transport.requests.Request()
    credentials.refresh(request)

    return credentials.token


async def send_fcm(tokens: list[str], title: str, body: str, data: dict | None = None):
    """Send push notifications using Firebase HTTP v1."""
    if not tokens:
        return

    access_token = get_access_token()

    url = f"https://fcm.googleapis.com/v1/projects/{FCM_PROJECT_ID}/messages:send"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; UTF-8",
    }

    # FCM v1 sends only one token per message
    for token in tokens:
        message = {
            "message": {
                "token": token,
                "notification": {"title": title, "body": body},
                "data": data or {},
            }
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=message, headers=headers)
            print("FCM Response:", res.text)
