# ------------------ modules/email_sender.py ------------------
import smtplib
import os
from email.message import EmailMessage
from datetime import datetime


def send_application_email(
    to_address: str,
    subject: str,
    body_text: str,
    attachments: list[str],
    from_address: str,
    app_password: str,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
) -> tuple[bool, str]:
    """
    Send an application e-mail with attachments (PDFs).

    Returns (success_bool, status_msg).
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address
    msg.set_content(body_text)

    for path in attachments:
        with open(path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype="application",
                subtype="pdf",
                filename=os.path.basename(path),
            )

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(from_address, app_password)
            smtp.send_message(msg)
        return True, f"Sent at {datetime.now():%Y-%m-%d %H:%M}"
    except Exception as exc:
        return False, f"Send failed: {exc}"
