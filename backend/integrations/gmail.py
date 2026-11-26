import os
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.message import EmailMessage

class GmailAdapter:
    """
    Gmail integration focused purely on the `gmail.modify` scope.
    Defaults to drafting emails rather than sending them, unless whitelisted.
    Uses behavioral profile for tone matching.
    """
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self):
        self.creds = None
        # In a real setup, you'd load token.json or run the OAuth flow here
        token_path = os.environ.get("GMAIL_TOKEN_PATH", "token.json")
        if os.path.exists(token_path):
            self.creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            self.service = build('gmail', 'v1', credentials=self.creds)
            self.is_connected = True
        else:
            self.service = None
            self.is_connected = False

    def create_draft(self, to_email: str, subject: str, body_text: str):
        """Creates an email draft in the user's inbox."""
        if not self.is_connected:
            print("Gmail is not connected. Missing token.json.")
            return None
            
        try:
            message = EmailMessage()
            message.set_content(body_text)
            message['To'] = to_email
            message['From'] = 'me'
            message['Subject'] = subject
            
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'message': {'raw': encoded_message}}
            
            draft = self.service.users().drafts().create(userId="me", body=create_message).execute()
            return draft['id']
        except Exception as e:
            print(f"Failed to create draft: {e}")
            return None
