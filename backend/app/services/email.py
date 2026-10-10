import smtplib
from email.message import EmailMessage

from app.core.config import settings

def send_email(to: str, subject: str, body: str) -> None:
    """Send an email. In development we only print it in the terminal."""
    if settings.EMAIL_BACKEND == "console":
        print("\n" + "=" * 60)
        print(f"EMAIL TO: {to}")
        print(f"SUBJECT:  {subject}")
        print(body)
        print("=" * 60 + "\n", flush=True)
        return

    # Real email using SMTP (Gmail, Mailtrap, ...)

    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)

def send_password_reset_email(to: str, token: str) -> None:
    send_email(
        to,
        "Reset your Foundary password",
        f"We received a request to reset your password.\n\nYour reset token:\n\n{token}\n\n"
        "Send it with your new password to POST /api/v1/auth/reset-password. "
        "It is valid for 30 minutes. If this was not you, ignore this email.",
    )

def send_verification_email(to: str, token: str) -> None:
    send_email(
        to,
        "Verify your Foundary account",
        f"Welcome to Foundary!\n\nYour verification token:\n\n{token}\n\n"
        "Send it to POST /api/v1/auth/verify-email. It is valid for 24 hours.",
    )