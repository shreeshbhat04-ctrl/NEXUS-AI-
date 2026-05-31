import base64
import logging
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from nexus_ai.config import get_settings

logger = logging.getLogger(__name__)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


class GoogleGmailAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _service(self, credentials: Credentials | None = None):
        if credentials is None:
            from nexus_ai.services.google_workspace import get_google_credentials
            credentials = get_google_credentials(GMAIL_SCOPES, "credentials/google_gmail_token.json")
        return build("gmail", "v1", credentials=credentials)

    def list_recent_health_emails(
        self,
        query: str = "lab report OR prescription OR diagnosis OR medical OR health",
        max_results: int = 5,
        credentials: Credentials | None = None,
    ) -> list[dict]:
        """Search the user's Gmail inbox for health-related emails."""
        service = self._service(credentials)
        try:
            result = service.users().messages().list(
                userId="me",
                q=query,
                maxResults=max_results,
            ).execute()
            messages = result.get("messages", [])
        except Exception as e:
            logger.error("Gmail list failed: %s", e)
            return []

        emails = []
        for msg_stub in messages:
            try:
                msg = service.users().messages().get(
                    userId="me",
                    id=msg_stub["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                ).execute()
                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                emails.append({
                    "id": msg["id"],
                    "subject": headers.get("Subject", "(no subject)"),
                    "from": headers.get("From", ""),
                    "date": headers.get("Date", ""),
                    "snippet": msg.get("snippet", ""),
                })
            except Exception as e:
                logger.warning("Failed to fetch message %s: %s", msg_stub["id"], e)
        return emails

    def send_care_summary(
        self,
        to: str,
        subject: str,
        body_html: str,
        credentials: Credentials | None = None,
    ) -> dict:
        """Send a care summary email from the patient's Gmail account."""
        service = self._service(credentials)
        message = MIMEText(body_html, "html")
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        try:
            sent = service.users().messages().send(
                userId="me",
                body={"raw": raw},
            ).execute()
            logger.info("Email sent: %s", sent.get("id"))
            return {"sent": True, "message_id": sent.get("id"), "error": None}
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            return {"sent": False, "message_id": None, "error": str(e)}
