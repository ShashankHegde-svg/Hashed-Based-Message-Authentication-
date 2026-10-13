"""
app.py
------
Backend for the HMAC-SHA256 lab, including the Sender/Receiver email demo.

Pages served:

    GET  /           role-selection home page
    GET  /sender     sender page: compose a message, seal it, email it
    GET  /receiver   receiver page: paste the email, verify the seal
    GET  /lab        the original single-page HMAC construction explorer

JSON API:

    POST /api/generate     produce a MAC for a message and key
    POST /api/verify       check a message, key and MAC against each other
    GET  /api/random-key   get a freshly generated random key
    POST /api/send         seal a message and email it to the receiver
    POST /api/parse-email  pull the message and MAC out of a pasted email

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

from email_service import (
    EmailConfigError,
    EmailSendError,
    parse_email_body,
    send_email,
)
from hmac_core import (
    generate_key,
    hmac_sha256_traced,
    verify_hmac_sha256,
)

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")

MAX_INPUT_CHARS = 100_000


def decode_hex_or_fail(value: str) -> bytes:
    """Parse a hex string, ignoring spaces, and raise ValueError if malformed."""
    cleaned = "".join(value.split())
    if len(cleaned) % 2 != 0:
        raise ValueError("a hex value must have an even number of characters")
    return bytes.fromhex(cleaned)


def read_field(payload: dict, name: str, encoding: str) -> bytes:
    """Pull one field out of the request body and turn it into bytes."""
    raw = payload.get(name, "")
    if not isinstance(raw, str):
        raise ValueError(f"{name} must be text")
    if len(raw) > MAX_INPUT_CHARS:
        raise ValueError(f"{name} is longer than the {MAX_INPUT_CHARS:,} character limit")
    if encoding == "hex":
        return decode_hex_or_fail(raw)
    return raw.encode("utf-8")


# ---------- pages ----------

@app.route("/")
def home():
    return send_from_directory(app.static_folder, "home.html")


@app.route("/sender")
def sender_page():
    return send_from_directory(app.static_folder, "sender.html")


@app.route("/receiver")
def receiver_page():
    return send_from_directory(app.static_folder, "receiver.html")


@app.route("/lab")
def lab_page():
    return send_from_directory(app.static_folder, "lab.html")


# ---------- HMAC API (shared by the lab, sender and receiver pages) ----------

@app.post("/api/generate")
def api_generate():
    payload = request.get_json(silent=True) or {}
    try:
        key = read_field(payload, "key", payload.get("keyEncoding", "text"))
        message = read_field(payload, "message", payload.get("messageEncoding", "text"))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    if not key:
        return jsonify({"error": "Enter a secret key before generating a MAC."}), 400

    result = hmac_sha256_traced(key, message)
    return jsonify(
        {
            "mac": result["tag"],
            "steps": result["steps"],
            "keyBytes": len(key),
            "messageBytes": len(message),
        }
    )


@app.post("/api/verify")
def api_verify():
    payload = request.get_json(silent=True) or {}
    try:
        key = read_field(payload, "key", payload.get("keyEncoding", "text"))
        message = read_field(payload, "message", payload.get("messageEncoding", "text"))
        candidate = decode_hex_or_fail(payload.get("mac", ""))
    except ValueError:
        return jsonify({"error": "The MAC must be a hex string, such as 64 hex characters."}), 400

    if not key:
        return jsonify({"error": "Enter the secret key that was used to create the MAC."}), 400
    if not candidate:
        return jsonify({"error": "Enter the MAC you want to check."}), 400

    valid = verify_hmac_sha256(key, message, candidate)
    expected = hmac_sha256_traced(key, message)["tag"]

    return jsonify(
        {
            "valid": valid,
            "expected": expected,
            "supplied": candidate.hex(),
            "reason": (
                "The message and key reproduce this MAC exactly."
                if valid
                else "The recomputed MAC does not match. The message, the key, or the MAC itself has changed."
            ),
        }
    )


@app.get("/api/random-key")
def api_random_key():
    return jsonify({"key": generate_key(32).hex()})


# ---------- Sender / Receiver email demo ----------

@app.post("/api/send")
def api_send():
    """
    Seal a message with HMAC-SHA256 and email it to the receiver.

    The email carries only the message and the MAC -- never the key. The key
    must reach the receiver through a separate channel, which is the point of
    the demonstration: email is treated as untrusted transport.
    """
    payload = request.get_json(silent=True) or {}
    try:
        key = read_field(payload, "key", payload.get("keyEncoding", "text"))
        message_text = payload.get("message", "")
        message = read_field(payload, "message", "text")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    receiver_email = (payload.get("receiverEmail") or "").strip()

    if not key:
        return jsonify({"error": "Enter the shared secret key before sealing the message."}), 400
    if not message:
        return jsonify({"error": "Enter a message to send."}), 400
    if "@" not in receiver_email or "." not in receiver_email.split("@")[-1]:
        return jsonify({"error": "Enter a valid receiver email address."}), 400

    result = hmac_sha256_traced(key, message)
    mac = result["tag"]

    try:
        send_email(receiver_email, message_text, mac)
    except EmailConfigError as error:
        return jsonify({"error": str(error), "mac": mac, "steps": result["steps"]}), 503
    except EmailSendError as error:
        return jsonify({"error": str(error), "mac": mac, "steps": result["steps"]}), 502

    return jsonify({"mac": mac, "steps": result["steps"], "sentTo": receiver_email})


@app.post("/api/parse-email")
def api_parse_email():
    """Pull the message and MAC out of a pasted copy of the sealed email."""
    payload = request.get_json(silent=True) or {}
    body = payload.get("body", "")
    if not isinstance(body, str) or not body.strip():
        return jsonify({"error": "Paste the email you received first."}), 400

    try:
        message, mac = parse_email_body(body)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"message": message, "mac": mac})


if __name__ == "__main__":
    # host="0.0.0.0" makes the app reachable from a phone on the same Wi-Fi,
    # and through a tunnel such as cloudflared or ngrok. See the README.
    #
    # Debug mode is OFF by default: with a public tunnel open, Flask's debugger
    # would be reachable by anyone holding the link. Set FLASK_DEBUG=1 in .env
    # only while developing locally.
    app.run(host="0.0.0.0", port=5000, debug=os.environ.get("FLASK_DEBUG") == "1")
