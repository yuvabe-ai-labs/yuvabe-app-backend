from src.core.config import settings
import httpx
from google.oauth2 import service_account
import google.auth.transport.requests

# Your Firebase project ID (from project settings)
FCM_PROJECT_ID = settings.FIREBASE_PROJECT_ID  # <-- change this


service_account_info = {
    "type": settings.FIREBASE_TYPE,
    "project_id": settings.FIREBASE_PROJECT_ID,
    "private_key_id": settings.FIREBASE_PRIVATE_KEY_ID,
    "private_key": settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n"),
    "client_email": settings.FIREBASE_CLIENT_EMAIL,
    "client_id": settings.FIREBASE_CLIENT_ID,
    "auth_uri": settings.FIREBASE_AUTH_URI,
    "token_uri": settings.FIREBASE_TOKEN_URI,
    "auth_provider_x509_cert_url": settings.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
    "client_x509_cert_url": settings.FIREBASE_CLIENT_X509_CERT_URL,
    "universe_domain": settings.FIREBASE_UNIVERSE_DOMAIN,
}


def get_access_token():
    """Generate OAuth2 access token for FCM HTTP v1."""
    scopes = ["https://www.googleapis.com/auth/firebase.messaging"]

    credentials = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=scopes
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
