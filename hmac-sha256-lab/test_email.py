"""
test_email.py
-------------
Tests for the email formatting and parsing helpers in email_service.py.
These never send a real email -- they only check that a message built by
build_email_body() can be parsed back out again by parse_email_body(), and
that obviously malformed input is rejected with a clear error.

Run with: python test_email.py
"""

from email_service import build_email_body, parse_email_body


def run_round_trip() -> int:
    failures = 0
    print("Round-trip: build then parse")

    cases = [
        ("Transfer 5000 to account 12345", "a1b2c3" * 10 + "ab"),
        ("multi\nline\nmessage", "00" * 32),
        ("", "ff" * 32),  # an empty message is still a message worth sealing
        ("  leading and trailing spaces  ", "11" * 32),
    ]

    for message, mac in cases:
        body = build_email_body(message, mac)
        parsed_message, parsed_mac = parse_email_body(body)
        ok = parsed_message == message and parsed_mac == mac
        failures += 0 if ok else 1
        label = message[:30].replace("\n", "\\n") or "(empty message)"
        print(f"  [{'pass' if ok else 'FAIL'}] {label!r}")
        if not ok:
            print(f"         expected message={message!r} mac={mac}")
            print(f"         got      message={parsed_message!r} mac={parsed_mac}")

    return failures


def run_malformed_checks() -> int:
    failures = 0
    print("\nMalformed input is rejected")

    malformed = [
        "no markers here at all",
        "-----BEGIN MESSAGE-----\nonly a begin marker",
        "-----BEGIN MESSAGE-----\nhi\n-----END MESSAGE-----\nno mac line here",
    ]
    for text in malformed:
        try:
            parse_email_body(text)
            ok = False
        except ValueError:
            ok = True
        failures += 0 if ok else 1
        print(f"  [{'pass' if ok else 'FAIL'}] rejects: {text[:40]!r}")

    return failures


if __name__ == "__main__":
    total = run_round_trip() + run_malformed_checks()
    print()
    if total == 0:
        print("All checks passed.")
    else:
        print(f"{total} check(s) failed.")
        raise SystemExit(1)
