import smtplib
from config import EMAIL, PASSWORD

from email.mime.text import MIMEText
import smtplib

EMAIL = "your_email@gmail.com"
PASSWORD = "your_app_password"

def send_email(to, subject, body):

    msg = MIMEText(body, "plain", "utf-8")   # ✅ UTF-8 FIX
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL, PASSWORD)

    server.sendmail(EMAIL, to, msg.as_string())  # ✅ FIXED

    server.quit()
    