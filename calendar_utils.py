import os
import pickle
import json
import streamlit as st
from tempfile import NamedTemporaryFile
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from dateutil.parser import isoparse
from datetime import timezone, datetime, timedelta

# ✅ Load REDIRECT_URI and SCOPES from Streamlit secrets or fallback to .env
REDIRECT_URI = st.secrets.get("GOOGLE_REDIRECT_URI") or os.getenv("GOOGLE_REDIRECT_URI")
SCOPES = [st.secrets.get("SCOPES") or os.getenv("SCOPES")]

# ✅ Write credentials JSON from secrets to a temp file
with NamedTemporaryFile(delete=False, suffix=".json") as tmp:
    tmp.write(st.secrets["GOOGLE_CREDENTIALS_JSON"].encode())
    CLIENT_SECRETS_FILE = tmp.name

# ✅ Step 1: Auth URL
def get_auth_url():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url

# ✅ Step 2: Exchange code for token
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

# ✅ Step 3: Load credentials
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

# ✅ Step 4: Build Calendar service
def get_calendar_service():
    creds = load_credentials()
    if creds:
        return build("calendar", "v3", credentials=creds)
    else:
        print("❌ Warning: Calendar service not available (no credentials)")
        return None

# ✅ Helper to check if authenticated
def is_authenticated():
    return os.path.exists("token.pkl")

# ✅ List events
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

# ✅ Create event
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

# ✅ Time availability check
def is_time_slot_free(start_time, end_time):
    service = get_calendar_service()
    if service is None:
        print("❌ Calendar service unavailable. Assuming time is free.")
        return True  # fallback to prevent breaking

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
        return True

# ✅ Book event
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
