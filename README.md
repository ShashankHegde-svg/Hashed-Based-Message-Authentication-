# HMAC-SHA256 Lab

**Send a message by email. Prove nobody changed it on the way.**

A full-stack web application that demonstrates message authentication using **HMAC-SHA256**. The sender generates a Message Authentication Code (MAC) using a shared secret key and sends the message and MAC through email. The receiver verifies the message using the same key. If the message has been modified during transmission, verification fails.

The HMAC construction is implemented manually based on **RFC 2104**, rather than using a ready-made HMAC library. SHA-256 is the only borrowed primitive, and the implementation is tested against the official **RFC 4231 test vectors**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Backend-Flask-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 Table of Contents

- [Why This Project?](#why-this-project)
- [Features](#features)
- [How It Works](#how-it-works)
- [Technology Stack](#technology-stack)
- [Installation and Setup](#installation-and-setup)
- [Configure Email](#configure-email)
- [Run the Tests](#run-the-tests)
- [Access the Application](#access-the-application)
- [Demonstration](#demonstration)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Security Notes and Limitations](#security-notes-and-limitations)
- [Troubleshooting](#troubleshooting)
- [References](#references)
- [License](#license)

---

## 🎯 Why This Project?

Email messages can potentially be read or modified during transmission. A simple hash cannot prevent tampering because an attacker can modify the message and calculate a new hash.

A **Message Authentication Code (MAC)** solves this problem by combining a secret key with the message. Only someone who knows the shared secret key should be able to generate a valid authentication tag.

This project demonstrates two important security properties:

- **Integrity:** Detects whether a message has been modified.
- **Authentication:** Verifies that the message was created by someone possessing the shared secret key.

Developed as a Cryptography and Network Security assignment, this project makes the HMAC algorithm visible and understandable rather than hiding its implementation behind a library call.

## ✨ Features

- **Sender and Receiver Interfaces:** Separate interfaces for sending and verifying messages.
- **Email Integration:** Sends messages and their authentication tags using SMTP.
- **Message Verification:** Automatically extracts the message and MAC from a pasted email.
- **Tampering Detection:** Demonstrates how changing even one character causes verification to fail.
- **Manual HMAC-SHA256 Implementation:** Implements key padding, `ipad`, `opad`, and the two-pass hash construction in `hmac_core.py`.
- **Constant-Time Comparison:** Uses constant-time comparison to reduce the risk of timing attacks.
- **HMAC Lab:** Displays intermediate values involved in generating the authentication tag.
- **Mobile-Friendly Interface:** Supports demonstrations using a laptop and mobile phone.
- **Automated Tests:** Includes unit tests and an end-to-end workflow test.

## 🔐 How It Works

HMAC-SHA256 generates an authentication tag using a secret key and a message.

### HMAC Formula

```text
HMAC(K, m) = H((K' XOR opad) || H((K' XOR ipad) || m))
```

Where:

- `H` is the SHA-256 hash function.
- `K` is the shared secret key.
- `K'` is the key adjusted to the hash function's 64-byte block size.
- `ipad` is the byte `0x36` repeated across the block.
- `opad` is the byte `0x5C` repeated across the block.
- `m` is the message.
- `||` represents concatenation.

The algorithm performs two hashing operations using differently derived key blocks. This construction provides message authentication and avoids the length-extension weakness associated with a naive construction such as `SHA256(key || message)`.

### Workflow

1. The sender and receiver securely share a secret key outside the email channel.
2. The sender enters a message, the secret key, and the receiver's email address.
3. The application calculates the HMAC-SHA256 authentication tag.
4. The message and authentication tag are sent through email. The secret key is not included in the email.
5. The receiver pastes the received email into the application and enters the same secret key.
6. The application recalculates the HMAC and compares it with the received tag.
7. If the tags match, the message is marked **Authentic**. Otherwise, it is marked **Not Authentic**.

**Important:** The secret key must be shared securely through a separate channel, such as an in-person exchange or a trusted communication channel.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Core programming language |
| Flask | Backend web framework |
| SHA-256 | Cryptographic hash primitive |
| HTML | Web page structure |
| CSS | Interface styling |
| JavaScript | Frontend interactions |
| SMTP | Email transmission |
| Python `unittest`-style test scripts | Testing the implementation and workflow |
| Git and GitHub | Version control and project hosting |

## 🚀 Installation and Setup

### Prerequisites

Make sure you have installed:

- Python 3.10 or newer
- Git
- A modern web browser

### Step 1: Clone the Repository

```bash
git clone https://github.com/ShashankHegde-svg/Hashed-Based-Message-Authentication-.git
```

Navigate to the project directory:

```bash
cd Hashed-Based-Message-Authentication-
```

> If the repository contains a nested `hmac-sha256-lab` directory, navigate into that directory before running the application.

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

For Windows Command Prompt:

```cmd
venv\Scripts\activate.bat
```

For macOS or Linux:

```bash
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Start the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

The application provides the following pages:

| Route | Description |
|---|---|
| `/` | Choose between sender and receiver |
| `/sender` | Generate an HMAC and send an email |
| `/receiver` | Extract and verify a received message |
| `/lab` | Explore the HMAC construction step by step |

Email sending requires SMTP configuration. Other supported functionality can be tested without configuring email.

## 📧 Configure Email

The application uses SMTP to send messages. Gmail can be configured using an App Password.

### Step 1: Enable Two-Step Verification

Enable two-step verification for your Google account.

### Step 2: Generate an App Password

Create an App Password through your Google Account settings.

Official page: https://myaccount.google.com/apppasswords

Use the generated App Password instead of your regular Google account password.

### Step 3: Configure Environment Variables

Copy `.env.example` to `.env` and add your SMTP configuration:

```ini
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.address@gmail.com
SMTP_PASS=your16characterapppassword
SMTP_FROM=your.address@gmail.com
```

Replace the example values with your own email address and App Password.

### Step 4: Restart the Application

Stop the running application and start it again:

```bash
python app.py
```

**Security warning:** Never commit your `.env` file or publish your email credentials. Keep `.env` in `.gitignore`.

For Outlook, the SMTP host can be configured as `smtp.office365.com`, using port `587`, subject to your account's SMTP settings.

## 🧪 Run the Tests

The project includes three test scripts.

### Test 1: HMAC-SHA256

```bash
python test_hmac.py
```

Checks the HMAC implementation against RFC 4231 test vectors and compares results with Python's standard HMAC implementation.

### Test 2: Email Parsing

```bash
python test_email.py
```

Tests email formatting and message extraction.

### Test 3: End-to-End Workflow

```bash
python test_flow.py
```

Tests the sender-to-receiver workflow using a simulated mail server, without sending a real email.

The workflow tests cover:

- Verification of an unchanged message.
- Detection of a modified message.
- Rejection of an incorrect secret key.
- Confirmation that the secret key is not included in the email.
- Handling of missing email configuration.

Each test script should report successful checks when all tests pass.

## 📱 Access the Application on a Phone

You can demonstrate the application using a laptop as the sender and a mobile phone as the receiver.

### Option 1: Cloudflare Tunnel

Install `cloudflared` on Windows:

```powershell
winget install --id Cloudflare.cloudflared
```

Restart the terminal after installation.

In the first terminal, start the application:

```powershell
python app.py
```

In a second terminal, run:

```powershell
cloudflared tunnel --url http://localhost:5000
```

The terminal will display a temporary HTTPS URL. Open that URL on your phone.

Keep both terminals running while using the application.

### Option 2: Same Wi-Fi Network

1. Connect the laptop and phone to the same Wi-Fi network.
2. Run `ipconfig` in PowerShell.
3. Find the laptop's IPv4 address.
4. Open the application on your phone using:

```text
http://YOUR_IPV4_ADDRESS:5000
```

Replace `YOUR_IPV4_ADDRESS` with the actual IPv4 address of your laptop.

Some college networks prevent devices from communicating directly, so a tunnel may be necessary.

**Security warning:** Stop the tunnel when your demonstration is finished. Anyone who obtains the public link may be able to access the sender interface. Do not expose the development application publicly for longer than necessary.

## 🎬 Demonstration

Follow these steps to demonstrate message authentication.

### Step 1: Share the Secret Key

Agree on a secret key with the receiver through a separate communication channel.

Example:

```text
class-demo-key
```

### Step 2: Send a Message

On the sender page:

1. Enter the receiver's email address.
2. Enter the secret key.
3. Enter a message, for example:

```text
Transfer 5000 to account 12345
```

4. Click **Seal and Send Email**.

The application generates the HMAC and sends the message with its authentication tag.

### Step 3: Verify the Message

On the receiver page:

1. Open the received email.
2. Copy its body.
3. Paste the content into the receiver interface.
4. Enter the same secret key.
5. Extract and verify the message.

Expected result:

```text
Authentic
```

### Step 4: Demonstrate Tampering

Change the message from:

```text
Transfer 5000 to account 12345
```

to:

```text
Transfer 9000 to account 12345
```

Verify the message again.

Expected result:

```text
Not Authentic
```

The calculated authentication tag no longer matches the tag received with the original message.

### Step 5: Test an Incorrect Key

Restore the original message and enter an incorrect secret key.

Expected result:

```text
Not Authentic
```

This demonstrates how HMAC-SHA256 detects message modifications and incorrect keys.

## 🔌 API Reference

The Flask application exposes the following endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/send` | Generates the MAC and sends an email |
| `POST` | `/api/parse-email` | Extracts the message and MAC from email text |
| `POST` | `/api/verify` | Verifies the message's authentication tag |
| `POST` | `/api/generate` | Generates an HMAC and returns intermediate values |
| `GET` | `/api/random-key` | Generates a random key |

### Generate an HMAC

Example request using `curl`:

```bash
curl -X POST http://127.0.0.1:5000/api/generate \
  -H "Content-Type: application/json" \
  -d "{\"key\":\"Jefe\",\"message\":\"what do ya want for nothing?\"}"
```

For the RFC 4231 test case using the key `Jefe` and the message `what do ya want for nothing?`, the expected HMAC-SHA256 value is:

```text
5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843
```

### API Parameters

Depending on the endpoint, requests can include:

- `key`: The shared secret key.
- `message`: The message to authenticate.
- `mac`: The authentication tag to verify.
- `receiverEmail`: The recipient's email address.
- `keyEncoding`: The key encoding, either `text` or `hex`.
- `messageEncoding`: The message encoding, either `text` or `hex`.
- `body`: The received email content.

Text values use UTF-8 encoding. Hexadecimal values use `hex` encoding.

Errors are returned as JSON objects containing an `error` field. The application uses HTTP status `400` for invalid input, `502` for email server rejection, and `503` when email is not configured.

## 📂 Project Structure

```text
Hashed-Based-Message-Authentication-/
│
├── app.py                  # Flask application and API endpoints
├── hmac_core.py            # Manual HMAC-SHA256 implementation
├── email_service.py        # Email formatting, parsing, and SMTP
├── requirements.txt        # Python dependencies
├── .env.example            # SMTP configuration template
├── .gitignore              # Files excluded from Git
│
├── static/
│   ├── home.html           # Home page
│   ├── sender.html         # Sender interface
│   ├── sender.js           # Sender-side JavaScript
│   ├── receiver.html       # Receiver interface
│   ├── receiver.js         # Receiver-side JavaScript
│   ├── lab.html            # HMAC learning interface
│   ├── app.js              # Frontend application logic
│   └── style.css           # Application styles
│
├── test_hmac.py            # HMAC test vectors and validation
├── test_email.py           # Email formatting and parsing tests
├── test_flow.py            # End-to-end workflow tests
│
└── docs/
    └── screenshots/        # Application screenshots
```

The exact directory structure may vary slightly depending on the files included in the repository.

## 🛡️ Security Notes and Limitations

This project is intended for educational purposes and demonstrates the principles of message authentication. It is not a production-ready email security system.

### 1. Shared Secret Reaches the Server

The sender and receiver interfaces transmit the shared key to the backend for HMAC calculation and verification. Although HTTPS protects data in transit when correctly configured, the server still processes the secret.

A production system should carefully consider where keys are stored and processed.

### 2. No Message Confidentiality

HMAC provides integrity and authentication, not encryption. The message itself is not hidden and may be readable by parties who can access the email.

### 3. No Non-Repudiation

Both sender and receiver possess the same secret key. Therefore, either party could generate a valid authentication tag.

Digital signatures are more appropriate when independent third parties must verify who signed a message.

### 4. Manual Email Verification

The receiver pastes the email content into the application. The application does not automatically access the receiver's inbox.

### 5. Limited Access Controls

The demonstration does not provide production-grade authentication or rate limiting on the sender interface. Avoid exposing it to untrusted users.

### 6. Development Server

Flask's built-in development server is intended for local development and testing. A production deployment requires an appropriate production server and additional security controls.

## 🐛 Troubleshooting

| Problem | Possible Solution |
|---|---|
| Email is not configured | Check that `.env` exists and is named correctly, then restart the application. |
| SMTP login fails | Verify your email address and use a valid App Password if required by your provider. |
| Email does not appear in the inbox | Check Spam and Promotions folders. |
| `cloudflared` is not recognized | Reopen the terminal after installation and verify that `cloudflared` is available in your PATH. |
| Phone cannot open the application | Ensure both terminals are running when using a tunnel and copy the complete URL. |
| Address already in use | Check whether another process is using port `5000`. |
| An unchanged message is marked Not Authentic | Confirm that both parties entered exactly the same key and message, including whitespace. |
| Tests fail | Check that dependencies are installed and that you are running commands from the project directory. |

## 📚 References

1. H. Krawczyk, M. Bellare, and R. Canetti, [RFC 2104: HMAC—Keyed-Hashing for Message Authentication](https://www.rfc-editor.org/rfc/rfc2104), 1997.
2. M. Nystrom, [RFC 4231: Identifiers and Test Vectors for HMAC-SHA-224/256/384/512](https://www.rfc-editor.org/rfc/rfc4231), 2005.
3. National Institute of Standards and Technology (NIST), *The Keyed-Hash Message Authentication Code (HMAC)*, FIPS 198-1, 2008.
4. National Institute of Standards and Technology (NIST), *Secure Hash Standard (SHS)*, FIPS 180-4, 2015.

## 📄 License

This project is released under the **MIT License**. See the `LICENSE` file for details.
