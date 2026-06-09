import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Fixes the strict scope validation crash when Google adds "openid" automatically
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

# The scopes we need for Drive and Calendar
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

def generate_tokens():
    print("Starting authentication flow...")
    print("Your browser should open automatically to ask for permission.")
    
    # Use the client secrets file we just copied over
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials/google_oauth_client.json', SCOPES)
    
    # Run the local server to handle the OAuth redirect
    creds = flow.run_local_server(port=0)
    
    # Save the generated credentials to the expected token files
    with open('credentials/google_drive_token.json', 'w') as token:
        token.write(creds.to_json())
        
    with open('credentials/google_calendar_token.json', 'w') as token:
        token.write(creds.to_json())
        
    with open('credentials/google_gmail_token.json', 'w') as token:
        token.write(creds.to_json())
        
    print("\n✅ Success! Tokens have been generated and saved to the credentials folder!")

if __name__ == '__main__':
    generate_tokens()
