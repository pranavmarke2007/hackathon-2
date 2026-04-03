from flask import Flask, jsonify, render_template, request
from email_reader import fetch_emails
from calendar_api import (
    check_availability, create_event, get_day_slots,
    suggest_alternatives, get_multi_user_availability
)
import dateparser
import re
import pytz
from config import DEFAULT_TIMEZONE

app = Flask(__name__)
IST = pytz.timezone(DEFAULT_TIMEZONE)

# 🔥 STORE STATE (status + alternatives)
processed_emails = {}

meeting_keywords = [
    "meeting", "schedule", "call",
    "discussion", "meet", "availability"
]

def is_meeting_related(text):
    return any(word in text.lower() for word in meeting_keywords)

def is_ambiguous(text):
    return not re.search(r'\b\d{1,2}[:\s]?\d{0,2}\s*(am|pm)\b', text.lower())


@app.route("/")
def home():
    return render_template("index.html")


# 🔥 INBOX (FINAL FIXED VERSION)
@app.route("/emails")
def get_all_emails():
    emails = fetch_emails()

    for mail in emails:
        body = mail["body"]
        sender = mail["from"]

        mail_id = mail.get("id") or body

        # ✅ RETURN STORED RESULT (NO REPROCESSING EVER)
        if mail_id in processed_emails:
            mail["status"] = processed_emails[mail_id]["status"]
            mail["alternatives"] = processed_emails[mail_id]["alternatives"]
            mail["tag"] = processed_emails[mail_id]["tag"]
            continue

        # 🔖 TAG
        tag = "📅 Meeting" if is_meeting_related(body) else "📩 General"
        mail["tag"] = tag

        # ❌ NOT MEETING
        if not is_meeting_related(body):
            status = "ℹ️ Not a meeting"
            processed_emails[mail_id] = {
                "status": status,
                "alternatives": [],
                "tag": tag
            }
            mail["status"] = status
            continue

        # ❓ AMBIGUOUS
        if is_ambiguous(body):
            status = "❓ Ambiguous"
            processed_emails[mail_id] = {
                "status": status,
                "alternatives": [],
                "tag": tag
            }
            mail["status"] = status
            continue

        # ⏱️ TIME EXTRACTION
        match = re.search(r'(\d{1,2}.*?(am|pm))', body.lower())
        time_text = match.group() if match else body

        meeting_time = dateparser.parse(
            time_text,
            settings={"PREFER_DATES_FROM": "future"}
        )

        if not meeting_time:
            status = "⚠️ Time not detected"
            processed_emails[mail_id] = {
                "status": status,
                "alternatives": [],
                "tag": tag
            }
            mail["status"] = status
            continue

        meeting_time = IST.localize(meeting_time)

        # 🔥 MAIN LOGIC
        if check_availability(meeting_time):
            create_event(meeting_time, attendee_emails=[sender])

            status = "✅ Scheduled"
            alternatives = []

        else:
            alternatives = suggest_alternatives(meeting_time)

            if alternatives:
                status = "🟡 Busy (Alternatives available)"
            else:
                status = "🔴 Busy"

        # 🔥 SAVE FINAL STATE (CRITICAL)
        processed_emails[mail_id] = {
            "status": status,
            "alternatives": alternatives,
            "tag": tag
        }

        mail["status"] = status
        mail["alternatives"] = alternatives

    return jsonify(emails)


# 👥 MULTI USER
@app.route("/multi_availability/<date>")
def multi_availability(date):
    participants = request.args.get("participants")

    if not participants:
        return jsonify({})

    participants = participants.split(",")

    data = get_multi_user_availability(date, participants)
    return jsonify(data)


# 📅 DAY SLOTS
@app.route("/day_slots/<date>")
def day_slots(date):
    return jsonify(get_day_slots(date))


if __name__ == "__main__":
    print("🚀 SERVER STARTING...")
    app.run(debug=True)