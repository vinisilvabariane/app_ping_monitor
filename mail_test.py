import os
import smtplib
from email.mime.text import MIMEText


def send_test_email() -> None:
    smtp_server = os.getenv("PM_SMTP_SERVER", "")
    smtp_port = int(os.getenv("PM_SMTP_PORT", "587"))
    sender_email = os.getenv("PM_SENDER_EMAIL", "")
    sender_password = os.getenv("PM_SENDER_PASSWORD", "")
    recipient_email = os.getenv("PM_RECIPIENT_EMAIL", "")

    if not all([smtp_server, sender_email, sender_password, recipient_email]):
        print(
            "Missing env vars. Set PM_SMTP_SERVER, PM_SENDER_EMAIL, PM_SENDER_PASSWORD and PM_RECIPIENT_EMAIL "
            "before running this script."
        )
        return

    msg = MIMEText("Ping Monitor test email sent successfully.")
    msg["Subject"] = "Ping Monitor - Test Email"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [recipient_email], msg.as_string())
        print("Email sent successfully.")
    except Exception as exc:
        print(f"Failed to send email: {exc}")


if __name__ == "__main__":
    send_test_email()
