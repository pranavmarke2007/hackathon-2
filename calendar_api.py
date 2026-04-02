from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def get_service():
    creds = Credentials.from_authorized_user_file("token.json")
    return build("calendar", "v3", credentials=creds)


def check_availability(start_time):
    service = get_service()
    end_time = start_time + timedelta(hours=1)

    events = service.events().list(
        calendarId='primary',
        timeMin=start_time.isoformat() + 'Z',
        timeMax=end_time.isoformat() + 'Z',
        singleEvents=True
    ).execute().get('items', [])

    return len(events) == 0


def create_event(start_time):
    service = get_service()
    end_time = start_time + timedelta(hours=1)

    event = {
        'summary': 'AI Scheduled Meeting',
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
    }

    service.events().insert(calendarId='primary', body=event).execute()


# 🔥 Suggest alternative slots
def suggest_alternatives(start_time):
    suggestions = []

    for i in range(1, 6):
        new_time = start_time + timedelta(hours=i)

        if check_availability(new_time):
            suggestions.append(new_time.strftime("%I:%M %p"))

    return suggestions


def get_day_slots(date_str):
    service = get_service()

    start = datetime.fromisoformat(date_str)
    end = start + timedelta(days=1)

    events = service.events().list(
        calendarId='primary',
        timeMin=start.isoformat() + 'Z',
        timeMax=end.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute().get('items', [])

    busy = []
    for e in events:
        s = e['start'].get('dateTime')
        e_ = e['end'].get('dateTime')
        if s and e_:
            busy.append((datetime.fromisoformat(s), datetime.fromisoformat(e_)))

    slots = []

    for h in range(9, 18):
        is_busy = False

        for s, e_ in busy:
            if s.hour <= h < e_.hour:
                is_busy = True

        slots.append({
            "hour": h,
            "display": f"{h%12 or 12} {'AM' if h<12 else 'PM'}",
            "status": "busy" if is_busy else "free"
        })

    return slots