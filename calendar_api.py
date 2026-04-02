from datetime import timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def get_service():
    creds = Credentials.from_authorized_user_file("token.json")
    return build("calendar", "v3", credentials=creds)

def check_availability(start_time):
    service = get_service()
    end_time = start_time + timedelta(hours=1)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_time.isoformat() + 'Z',
        timeMax=end_time.isoformat() + 'Z',
        singleEvents=True
    ).execute()

    events = events_result.get('items', [])

    return len(events) == 0


def create_event(start_time):
    service = get_service()
    end_time = start_time + timedelta(hours=1)

    event = {
        'summary': 'AI Scheduled Meeting',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Kolkata'
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Kolkata'
        },
    }

    service.events().insert(
        calendarId='primary',
        body=event
    ).execute()