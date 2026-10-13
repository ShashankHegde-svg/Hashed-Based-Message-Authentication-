"""
test_flow.py
------------
End-to-end test of the sender -> email -> receiver flow, with no real email.

smtplib.SMTP is replaced by a fake that records what would have been sent.
The test then takes that captured email, runs it through the receiver's
parse-email and verify endpoints, and checks both outcomes: an untouched
email verifies, and an email tampered with in transit does not.

Run with: python test_flow.py
"""

import email
import os
from unittest.mock import patch

os.environ.update(
    SMTP_HOST="smtp.test", SMTP_PORT="587", SMTP_USER="sender@test.example",
    SMTP_PASS="not-a-real-password",
)

from app import app  # noqa: E402  (env must be set before import)

KEY = "agreed-beforehand"
MESSAGE = "Transfer 5000 to account 12345"
sent_emails = []


class FakeSMTP:
    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port
    def __enter__(self): return self
    def __exit__(self, *exc): return False
    def starttls(self): pass
    def login(self, user, password): self.login_used = (user, password)
    def sendmail(self, sender, recipients, raw):
        sent_emails.append({"from": sender, "to": recipients, "raw": raw})


def check(description, ok):
    print(f"  [{'pass' if ok else 'FAIL'}] {description}")
    return 0 if ok else 1


def body_of(raw: str) -> str:
    return email.message_from_string(raw).get_payload(0).get_payload(decode=True).decode()


def run() -> int:
    failures = 0
    client = app.test_client()

    print("Sender")
    with patch("email_service.smtplib.SMTP", FakeSMTP):
        reply = client.post("/api/send", json={
            "receiverEmail": "receiver@test.example", "key": KEY,
            "keyEncoding": "text", "message": MESSAGE})
    data = reply.get_json()
    failures += check("send succeeds", reply.status_code == 200)
    failures += check("exactly one email was sent", len(sent_emails) == 1)
    failures += check("addressed to the receiver", sent_emails[0]["to"] == ["receiver@test.example"])
    body = body_of(sent_emails[0]["raw"])
    failures += check("email contains the message", MESSAGE in body)
    failures += check("email contains the MAC", data["mac"] in body)
    failures += check("the secret key is NOT in the email", KEY not in sent_emails[0]["raw"])

    print("\nReceiver, untouched email")
    parsed = client.post("/api/parse-email", json={"body": body}).get_json()
    failures += check("message extracted intact", parsed["message"] == MESSAGE)
    verdict = client.post("/api/verify", json={
        "key": KEY, "keyEncoding": "text", "message": parsed["message"],
        "messageEncoding": "text", "mac": parsed["mac"]}).get_json()
    failures += check("reads Authentic", verdict["valid"] is True)

    print("\nReceiver, email tampered with in transit")
    tampered = body.replace("5000", "9000")
    parsed = client.post("/api/parse-email", json={"body": tampered}).get_json()
    verdict = client.post("/api/verify", json={
        "key": KEY, "keyEncoding": "text", "message": parsed["message"],
        "messageEncoding": "text", "mac": parsed["mac"]}).get_json()
    failures += check("reads Not authentic", verdict["valid"] is False)

    print("\nReceiver, wrong key")
    parsed = client.post("/api/parse-email", json={"body": body}).get_json()
    verdict = client.post("/api/verify", json={
        "key": "guessed-wrong", "keyEncoding": "text", "message": parsed["message"],
        "messageEncoding": "text", "mac": parsed["mac"]}).get_json()
    failures += check("reads Not authentic", verdict["valid"] is False)

    print("\nError handling")
    bad = client.post("/api/send", json={"receiverEmail": "nope", "key": KEY, "message": MESSAGE})
    failures += check("rejects an invalid email address", bad.status_code == 400)
    empty = client.post("/api/send", json={"receiverEmail": "a@b.co", "key": KEY, "message": ""})
    failures += check("rejects an empty message", empty.status_code == 400)

    saved = {k: os.environ.pop(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS")}
    unconfigured = client.post("/api/send", json={"receiverEmail": "a@b.co", "key": KEY, "message": MESSAGE})
    os.environ.update(saved)
    failures += check("reports missing email setup clearly", unconfigured.status_code == 503)
    failures += check("still returns the MAC when email is unconfigured", "mac" in unconfigured.get_json())
    return failures


if __name__ == "__main__":
    total = run()
    print("\nAll checks passed." if total == 0 else f"\n{total} check(s) failed.")
    raise SystemExit(1 if total else 0)
