import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from api.core.config import Settings, get_settings

log = logging.getLogger(__name__)


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class LogMailer:
    """For local work only: the message, reset link included, goes to the server log."""

    def send(self, to: str, subject: str, body: str) -> None:
        log.warning("Email to %s: %s\n%s", to, subject, body)


class SmtpMailer:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=20) as smtp:
                smtp.starttls()
                if self.settings.smtp_user:
                    smtp.login(self.settings.smtp_user, self.settings.smtp_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException):
            # Runs after the response is sent, so the failure is only logged; the address is not.
            log.exception("Sending email failed")


def get_mailer() -> Mailer:
    settings = get_settings()
    return SmtpMailer(settings) if settings.mail_backend == "smtp" else LogMailer()
