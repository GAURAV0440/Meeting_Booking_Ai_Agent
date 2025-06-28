import os
import pickle
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from dateutil.parser import isoparse
from datetime import timezone, datetime, timedelta

load_dotenv()

SCOPES = [os.getenv("SCOPES")]
CLIENT_SECRETS_FILE = "credentials.json"
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


def get_auth_url():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url


def exchange_code_for_token(code):
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(code=code)

    credentials = flow.credentials
    with open("token.pkl", "wb") as token_file:
        pickle.dump(credentials, token_file)
    return credentials


def load_credentials():
    if os.path.exists("token.pkl"):
        with open("token.pkl", "rb") as token_file:
            credentials = pickle.load(token_file)

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            with open("token.pkl", "wb") as token_file:
                pickle.dump(credentials, token_file)

        return credentials
    return None


def get_calendar_service():
    creds = load_credentials()
    if creds:
        return build("calendar", "v3", credentials=creds)
    else:
        print("❌ Warning: Calendar service not available (no credentials)")
        return None


def list_events():
    service = get_calendar_service()
    if service is None:
        print("❌ Calendar service not available. Cannot list events.")
        return []
    try:
        events_result = service.events().list(
            calendarId='primary',
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    except Exception as e:
        print(f'An error occurred while listing events: {e}')
        return []


def create_event(start_time, end_time, summary="TailorTalk Meeting", description="Auto-booked by TailorTalk Bot", invitees=None):
    service = get_calendar_service()
    if service is None:
        raise Exception("❌ Cannot create event: Calendar service not available.")

    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'},
    }

    if invitees:
        event['attendees'] = [{'email': email.strip()} for email in invitees if email]

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return event.get('htmlLink')
    except Exception as e:
        print(f"❌ Failed to create event: {e}")
        raise


def is_time_slot_free(start_time, end_time):
    service = get_calendar_service()
    if service is None:
        print("❌ Calendar service unavailable. Assuming time is free.")
        return True  # <-- assumes free if can't check

    try:
        time_min = isoparse(start_time).astimezone(timezone.utc).isoformat()
        time_max = isoparse(end_time).astimezone(timezone.utc).isoformat()

        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        return len(events) == 0

    except Exception as e:
        print(f'An error occurred while checking time slot: {e}')
        return True  # <-- fallback to prevent breaking


def book_event_at(start_time_obj, duration_minutes, description, invitees=None):
    service = get_calendar_service()
    if service is None:
        raise Exception("❌ Cannot book event: Calendar service not available.")

    end_time_obj = start_time_obj + timedelta(minutes=duration_minutes)

    event = {
        'summary': "TailorTalk Meeting",
        'description': description,
        'start': {'dateTime': start_time_obj.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time_obj.isoformat(), 'timeZone': 'Asia/Kolkata'},
    }

    if invitees:
        event['attendees'] = [{'email': email.strip()} for email in invitees if email]

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return {
            "link": event.get("htmlLink"),
            "start": start_time_obj.isoformat(),
            "end": end_time_obj.isoformat()
        }
    except Exception as e:
        print(f"❌ Booking failed: {e}")
        raise
