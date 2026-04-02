import smtplib
from config import EMAIL, PASSWORD

def send_email(to, subject, message):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)

    msg = f"Subject: {subject}\n\n{message}"
    server.sendmail(EMAIL, to, msg)

    server.quit()