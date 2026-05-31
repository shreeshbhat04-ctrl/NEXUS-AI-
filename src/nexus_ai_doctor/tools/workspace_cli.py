import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

class WorkspaceCLI:
    def __init__(self, service_account_file: str = None):
        if not service_account_file:
            service_account_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not service_account_file or not os.path.exists(service_account_file):
            raise ValueError("Service account credentials not provided or found.")
            
        scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]
        
        self.creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )
        
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.gmail_service = build('gmail', 'v1', credentials=self.creds)

    def create_calendar_event(self, calendar_id: str, summary: str, start_time: str, end_time: str, description: str = ""):
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }
        event = self.calendar_service.events().insert(calendarId=calendar_id, body=event).execute()
        return event.get('htmlLink')

    def list_calendar_events(self, calendar_id: str, max_results: int = 10):
        events_result = self.calendar_service.events().list(
            calendarId=calendar_id, 
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return events

    def send_email(self, to: str, subject: str, message_text: str, user_id: str = 'me'):
        from email.message import EmailMessage
        import base64
        
        message = EmailMessage()
        message.set_content(message_text)
        message['To'] = to
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        
        send_message = self.gmail_service.users().messages().send(
            userId=user_id, body=create_message
        ).execute()
        return send_message
