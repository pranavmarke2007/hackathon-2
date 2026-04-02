from flask import Flask, jsonify, render_template
from email_reader import fetch_emails
from calendar_api import check_availability, create_event, get_day_slots, suggest_alternatives
from email_sender import send_email
from datetime import datetime
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/emails")
def get_emails():
    import dateparser
    import re

    emails = fetch_emails()

    for mail in emails:
        body = mail["body"]
        sender = mail["from"]

        print("BODY:", body)

        # 🔥 Extract time
        match = re.search(r'(\d{1,2}.*?(am|pm))', body.lower())

        if match:
            time_text = match.group()
        else:
            time_text = body

        print("EXTRACTED:", time_text)

        meeting_time = dateparser.parse(
            time_text,
            settings={
                "PREFER_DATES_FROM": "future",
                "RELATIVE_BASE": datetime.now()
            }
        )

        print("PARSED:", meeting_time)

        if meeting_time:

            free = check_availability(meeting_time)

            if free:
                # ✅ BOOK SLOT
                create_event(meeting_time)

                send_email(
                    sender,
                    "Meeting Confirmed",
                    f" Your meeting is scheduled at {meeting_time.strftime('%I:%M %p on %d %B')}"
                )

                mail["status"] = "✅ Scheduled"

            else:
                # ❌ SLOT ALREADY BOOKED
                alternatives = suggest_alternatives(meeting_time)

                alt_text = "\n".join(alternatives) if alternatives else "No slots available"

                send_email(
                    sender,
                    "Slot Already Scheduled",
                    f""" This slot is already scheduled.

                        Suggested free slots:
                        {alt_text}
                        """
                )

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