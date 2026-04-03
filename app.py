from flask import Flask, jsonify, render_template
from email_reader import fetch_emails
from calendar_api import check_availability, create_event, get_day_slots, suggest_alternatives
from email_sender import send_email
from datetime import datetime
import dateparser
import re

app = Flask(__name__)

processed_emails = set()   # ✅ ADD THIS


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/emails")
def get_emails():

    emails = fetch_emails()
    booked_slots = set()

    for mail in emails:

        body = mail["body"]
        sender = mail["from"]

        # ✅ unique id
        mail_id = mail.get("id") or body

        if mail_id in processed_emails:
            print("Already processed")
            continue

        print("BODY:", body)

        # 🔥 Extract time
        match = re.search(r'(\d{1,2}.*?(am|pm))', body.lower())

        if match:
            time_text = match.group()
        else:
            time_text = body

        print("EXTRACTED:", time_text)

        # 🔥 Parse time
        meeting_time = dateparser.parse(
            time_text,
            settings={
                "PREFER_DATES_FROM": "future",
                "RELATIVE_BASE": datetime.now()
            }
        )

        print("PARSED:", meeting_time)

        if meeting_time:

            slot_key = meeting_time.strftime("%Y-%m-%d %H:%M")

            # 🔴 prevent duplicates in same run
            if slot_key in booked_slots:
                mail["status"] = "❌ Duplicate (same batch)"
                continue

            free = check_availability(meeting_time)

            if free:
                create_event(meeting_time)
                booked_slots.add(slot_key)

                send_email(
                    sender,
                    "Meeting Confirmed",
                    f"Your meeting is scheduled at {meeting_time.strftime('%I:%M %p on %d %B')}"
                )

                processed_emails.add(mail_id)   # ✅ CORRECT PLACE

                mail["status"] = "✅ Scheduled"

            else:
                alternatives = suggest_alternatives(meeting_time)

                alt_text = "\n".join(alternatives) if alternatives else "No slots available"

                send_email(
                    sender,
                    "Slot Already Scheduled",
                    f"""This slot is already booked.

Suggested free slots:
{alt_text}
"""
                )

                processed_emails.add(mail_id)   # ✅ CORRECT PLACE

                mail["status"] = "❌ Already Scheduled + Alternatives Sent"

        else:
            mail["status"] = "⚠️ Time not detected"

    return jsonify(emails)


@app.route("/day_slots/<date>")
def day_slots(date):
    return jsonify(get_day_slots(date))


if __name__ == "__main__":
    print("SERVER STARTING...")
    app.run(debug=True)