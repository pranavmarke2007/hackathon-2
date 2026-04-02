from flask import Flask, jsonify, render_template
from email_reader import fetch_emails
from parser import extract_time
from calendar_api import check_availability, create_event
from email_sender import send_email

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/emails")
def get_emails():
    emails = fetch_emails()

    for mail in emails:
        body = mail["body"]
        sender = mail["from"]

        if "meeting" in body.lower() or "free" in body.lower():
            meeting_time = extract_time(body)

            if meeting_time:
                free = check_availability(meeting_time)

                if free:
                    create_event(meeting_time)
                    send_email(sender, "Meeting Confirmed", f"I am free at {meeting_time}")
                    mail["status"] = "✅ Scheduled"
                else:
                    send_email(sender, "Not Available", "I am not free at that time")
                    mail["status"] = "❌ Busy"
            else:
                mail["status"] = "⚠️ Time not detected"
        else:
            mail["status"] = "Ignored"

    return jsonify(emails)

if __name__ == "__main__":
    app.run(debug=True)
from calendar_api import get_busy_slots

@app.route("/calendar")
def calendar():
    return jsonify(get_busy_slots())    
print("BODY:", body)
print("TIME:", meeting_time)
