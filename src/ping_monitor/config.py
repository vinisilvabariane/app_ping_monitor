import os
from dataclasses import dataclass, field


@dataclass
class EmailConfig:
    smtp_server: str = field(default_factory=lambda: os.getenv("PM_SMTP_SERVER", ""))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("PM_SMTP_PORT", "587")))
    sender_email: str = field(default_factory=lambda: os.getenv("PM_SENDER_EMAIL", ""))
    sender_password: str = field(default_factory=lambda: os.getenv("PM_SENDER_PASSWORD", ""))
    recipient_email: str = field(default_factory=lambda: os.getenv("PM_RECIPIENT_EMAIL", ""))

    def enabled(self) -> bool:
        return all(
            [self.smtp_server, self.smtp_port, self.sender_email, self.sender_password, self.recipient_email]
        )
