import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def test_google_apis():
    print("Testing Google Calendar API...")
    try:
        # Load Calendar token
        creds_cal = Credentials.from_authorized_user_file('credentials/google_calendar_token.json')
        service_cal = build('calendar', 'v3', credentials=creds_cal)
        
        # Call the Calendar API
        events_result = service_cal.events().list(calendarId='primary', maxResults=1, singleEvents=True,
                                                  orderBy='startTime').execute()
        events = events_result.get('items', [])
        print(f"✅ Calendar Success! Found {len(events)} upcoming events.")
    except Exception as e:
        print(f"❌ Calendar Failed: {e}")

    print("\nTesting Google Drive API...")
    try:
        # Load Drive token
        creds_drive = Credentials.from_authorized_user_file('credentials/google_drive_token.json')
        service_drive = build('drive', 'v3', credentials=creds_drive)
        
        # Call the Drive API
        results = service_drive.files().list(pageSize=1, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        print(f"✅ Drive Success! Found {len(items)} files.")
    except Exception as e:
        print(f"❌ Drive Failed: {e}")

    print("\nTesting Google Gmail API...")
    try:
        # Load Gmail token
        creds_gmail = Credentials.from_authorized_user_file('credentials/google_gmail_token.json')
        service_gmail = build('gmail', 'v1', credentials=creds_gmail)
        
        # Call the Gmail API
        results = service_gmail.users().messages().list(userId='me', maxResults=1).execute()
        messages = results.get('messages', [])
        print(f"✅ Gmail Success! Found {len(messages)} messages.")
    except Exception as e:
        print(f"❌ Gmail Failed: {e}")

if __name__ == '__main__':
    test_google_apis()
