import logging
from dataclasses import dataclass
from nexus_ai.adapters.gmail import GoogleGmailAdapter

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    channel: str
    delivery_status: str


class MockNotificationAdapter:
    def __init__(self) -> None:
        self.gmail_adapter = GoogleGmailAdapter()

    def send(self, channel: str, message_body: str) -> NotificationResult:
        logger.info(f"Notification triggered on channel [{channel}]: {message_body}")
        
        status = "sent"
        if channel == "gmail":
            # Attempt to send via Gmail adapter if configured
            try:
                # We send a mock/real alert to the user's gmail address (or fallback)
                logger.info(f"[GMAIL NOTIFICATION] Sending email: {message_body}")
                # We can also attempt a default send, or just log it
            except Exception as e:
                logger.warning(f"Gmail notifications delivery failed: {e}")
        elif channel == "sms":
            # Mock Twilio SMS log
            logger.info(f"[SMS NOTIFICATION] Sent SMS alert: {message_body}")
        elif channel == "web":
            # Mock Web Toast/Notification log
            logger.info(f"[WEB NOTIFICATION] Dispatched web alert: {message_body}")
            
        return NotificationResult(channel=channel, delivery_status=status)

