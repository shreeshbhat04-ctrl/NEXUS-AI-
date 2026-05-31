from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from nexus_ai.config import get_settings


def get_google_credentials(scopes: list[str], token_file_path: str) -> Credentials:
    settings = get_settings()
    client_file = Path(settings.google_oauth_client_file)
    token_file = Path(token_file_path)

    creds: Credentials | None = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_file), scopes)
        creds = flow.run_local_server(port=0)

    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


def credentials_from_tokens(
    access_token: str,
    refresh_token: str | None = None,
    token_uri: str = "https://oauth2.googleapis.com/token",
    client_id: str | None = None,
    client_secret: str | None = None,
    scopes: list[str] | None = None,
) -> Credentials:
    """Build Google Credentials from raw OAuth tokens (browser flow)."""
    settings = get_settings()
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id or settings.google_oauth_client_id,
        client_secret=client_secret or settings.google_oauth_client_secret,
        scopes=scopes,
    )
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

