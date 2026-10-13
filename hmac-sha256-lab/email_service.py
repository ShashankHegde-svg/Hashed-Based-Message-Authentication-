"""
email_service.py
-----------------
Sends the sealed message (the plaintext message plus its HMAC-SHA256 tag) to
the receiver by email, and provides the plain-text formatting used for that
email so the receiver's page can parse the two fields back out of a pasted
copy of the message.

Email is only the transport in this demonstration -- exactly as unprotected
as any other channel an attacker might intercept or tamper with. The HMAC is
what lets the receiver detect whether the message changed in transit; the
email itself offers no protection on its own. This is the point the
sender/receiver demo exists to make.

SMTP credentials are read from environment variables (see .env.example) and
are never hard-coded here or sent to the browser.
"""

import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BEGIN_MARKER = "-----BEGIN MESSAGE-----"
END_MARKER = "-----END MESSAGE-----"
MAC_PREFIX = "MAC (HMAC-SHA256, hex): "


class EmailConfigError(RuntimeError):
    """Raised when the SMTP settings needed to send mail are missing."""


class EmailSendError(RuntimeError):
    """Raised when the SMTP server rejects the login or the message."""


def build_email_body(message_text: str, mac_hex: str) -> str:
    """
    Build the plain-text email body carrying the message and its tag.

    The BEGIN/END markers and the MAC line are fixed and machine-parseable,
    so the receiver's page can extract both fields automatically from a
    pasted copy of the email, while the email still reads plainly to a human
    looking straight at their inbox.
    """
    return (
        "You have received a message authenticated with HMAC-SHA256.\n\n"
        f"{BEGIN_MARKER}\n"
        f"{message_text}\n"
        f"{END_MARKER}\n"
        f"{MAC_PREFIX}{mac_hex}\n\n"
        "To check this message: open the Receiver page of the HMAC lab, enter "
        "the secret key you already share with the sender (sent through a "
        "separate channel -- never through this email), paste this whole "
        "email into the box provided, and press Verify.\n"
    )


def parse_email_body(body: str) -> tuple[str, str]:
    """
    Reverse build_email_body(): pull the message and the hex MAC back out of
    a pasted email. Raises ValueError if either part cannot be found.
    """
    begin = body.find(BEGIN_MARKER)
    end = body.find(END_MARKER)
    if begin == -1 or end == -1 or end <= begin:
        raise ValueError("Could not find the message markers in the pasted text.")

    message_text = body[begin + len(BEGIN_MARKER):end]
    # build_email_body always inserts exactly one newline on each side of the
    # message; strip only those two, so a message that itself starts or ends
    # with a blank line is preserved rather than silently trimmed.
    if message_text.startswith("\n"):
        message_text = message_text[1:]
    if message_text.endswith("\n"):
        message_text = message_text[:-1]

    mac_match = re.search(re.escape(MAC_PREFIX) + r"([0-9a-fA-F]+)", body)
    if not mac_match:
        raise ValueError("Could not find a MAC in the pasted text.")

    return message_text, mac_match.group(1)


def send_email(receiver_email: str, message_text: str, mac_hex: str) -> None:
    """
    Send the sealed message to receiver_email over SMTP.

    Reads SMTP_HOST, SMTP_PORT, SMTP_USER and SMTP_PASS from the environment
    (see .env.example); SMTP_FROM is optional and defaults to SMTP_USER.
    Raises EmailConfigError if the required settings are missing, or
    EmailSendError if the SMTP server rejects the attempt.
    """
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")

    if not host or not user or not password:
        raise EmailConfigError(
            "Email is not configured on the server. Set SMTP_HOST, SMTP_USER "
            "and SMTP_PASS in a .env file (see .env.example) and restart the "
            "server."
        )

    port = int(os.environ.get("SMTP_PORT", "587"))
    sender = os.environ.get("SMTP_FROM", user)

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver_email
    msg["Subject"] = "A message sealed with HMAC-SHA256"
    msg.attach(MIMEText(build_email_body(message_text, mac_hex), "plain"))

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, [receiver_email], msg.as_string())
    except smtplib.SMTPAuthenticationError as error:
        raise EmailSendError(
            "The mail server rejected the sender's login. If this is a Gmail "
            "account, SMTP_PASS must be an App Password, not the normal "
            "account password -- see the README for how to create one."
        ) from error
    except (smtplib.SMTPException, OSError) as error:
        raise EmailSendError(f"The email could not be sent: {error}") from error
