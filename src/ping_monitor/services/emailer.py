import smtplib
from email.mime.text import MIMEText

from ping_monitor.config import EmailConfig


ALERT_SUBJECT = "Ping Monitor Alert: devices offline"


class EmailAlertService:
    def __init__(self, config: EmailConfig):
        self.config = config

    def send_offline_alert(self, offline_hosts: list[str]) -> tuple[bool, str]:
        if not self.config.enabled():
            return (
                False,
                "Email alert skipped. Configure PM_SMTP_SERVER, PM_SMTP_PORT, "
                "PM_SENDER_EMAIL, PM_SENDER_PASSWORD and PM_RECIPIENT_EMAIL.",
            )

        body = "These hosts are offline:\n\n" + "\n".join(offline_hosts)
        message = MIMEText(body)
        message["Subject"] = ALERT_SUBJECT
        message["From"] = self.config.sender_email
        message["To"] = self.config.recipient_email

        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
                server.sendmail(
                    self.config.sender_email,
                    [self.config.recipient_email],
                    message.as_string(),
                )
            return True, "Email alert sent successfully."
        except Exception as exc:
            return False, f"Email alert failed: {exc}"
