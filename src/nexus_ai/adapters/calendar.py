from datetime import datetime, timedelta

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from nexus_ai.config import get_settings
from nexus_ai.services.google_workspace import get_google_credentials

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _service(self, credentials: Credentials | None = None):
        creds = credentials or get_google_credentials(CALENDAR_SCOPES, self.settings.google_calendar_token_file)
        return build("calendar", "v3", credentials=creds)

    def list_upcoming_events(self, max_results: int = 10, credentials: Credentials | None = None) -> list[dict]:
        service = self._service(credentials)
        response = (
            service.events()
            .list(
                calendarId=self.settings.google_calendar_id,
                timeMin=datetime.utcnow().isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return response.get("items", [])

    def create_demo_event(
        self,
        summary: str,
        minutes_from_now: int = 30,
        duration_minutes: int = 30,
        credentials: Credentials | None = None,
    ) -> dict:
        service = self._service(credentials)
        start = datetime.utcnow() + timedelta(minutes=minutes_from_now)
        end = start + timedelta(minutes=duration_minutes)
        event = {
            "summary": summary,
            "start": {"dateTime": start.isoformat() + "Z", "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat() + "Z", "timeZone": "UTC"},
        }
        created = service.events().insert(calendarId=self.settings.google_calendar_id, body=event).execute()
        return created
