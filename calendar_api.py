from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pytz

IST = pytz.timezone('Asia/Kolkata')


def get_service():
    creds = Credentials.from_authorized_user_file("token.json")
    return build("calendar", "v3", credentials=creds)


# ✅ FIXED AVAILABILITY CHECK
def check_availability(start_time):
    service = get_service()

    # 🔥 make timezone aware
    start_time = IST.localize(start_time)
    end_time = start_time + timedelta(hours=1)

    events = service.events().list(
        calendarId='primary',
        timeMin=start_time.isoformat(),
        timeMax=end_time.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute().get('items', [])

    return len(events) == 0


# ✅ CREATE EVENT
def create_event(start_time):
    service = get_service()

    start_time = IST.localize(start_time)
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

    service.events().insert(calendarId='primary', body=event).execute()


# ✅ SUGGEST ALTERNATIVES
def suggest_alternatives(start_time):
    suggestions = []

    current = start_time.replace(minute=0, second=0, microsecond=0)

    for day in range(0, 2):

        base_day = current + timedelta(days=day)

        for hour in range(9, 17):   # 9 AM to 5 PM

            new_time = base_day.replace(hour=hour)

            if new_time <= datetime.now():
                continue

            if new_time == start_time:
                continue

            if check_availability(new_time):
                suggestions.append(new_time.strftime("%d %B %I:%M %p"))

            if len(suggestions) >= 5:
                return suggestions

    return suggestions


# ✅ DAY SLOTS FIXED
def get_day_slots(date_str):
    service = get_service()

    start = IST.localize(datetime.fromisoformat(date_str))
    end = start + timedelta(days=1)

    events = service.events().list(
        calendarId='primary',
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
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
                break

        slots.append({
            "hour": h,
            "display": f"{h%12 or 12} {'AM' if h<12 else 'PM'}",
            "status": "busy" if is_busy else "free"
        })

    return slots