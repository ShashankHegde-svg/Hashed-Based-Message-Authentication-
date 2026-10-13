# HMAC-SHA256 Lab — Sender and Receiver

A web application where one person (the **sender**) seals a message with
HMAC-SHA256 and emails it, and another (the **receiver**) checks the seal.
The HMAC construction is implemented from RFC 2104, not taken from a library.

Submitted for: Cryptography and Network Security.

## Pages

| URL | Purpose |
|---|---|
| `/` | Choose a role |
| `/sender` | Type a message, seal it with the shared key, email it |
| `/receiver` | Paste the received email, enter the key, verify |
| `/lab` | The original single-page explorer showing every step of HMAC |

## The idea being demonstrated

Email is **untrusted transport**: anyone between sender and receiver could edit
the message. HMAC lets the receiver detect that, provided the two share a
secret key that never travelled in the email.

1. Sender and receiver agree on a key **out of band** (aloud, or in a chat app).
2. Sender seals the message. The email contains the message and the MAC, never the key.
3. Receiver pastes the email, enters the key, presses Verify. Untouched: **Authentic**.
4. Edit one character of the message before verifying (playing the attacker): **Not authentic**.

---

## Part 1 — One-time setup (Windows + VS Code)

Do steps 1–4 from the earlier guide (open the folder in VS Code, create and
activate `venv`, select the interpreter), then:

```
pip install -r requirements.txt
python test_hmac.py
python test_email.py
python test_flow.py
```

All three should end with "All checks passed." `test_flow.py` runs the whole
sender → email → receiver flow against a fake mail server, including a
tampered email being rejected.

## Part 2 — Set up email sending

The server sends mail through your own mail account over SMTP. The easiest
route is Gmail.

**Create a Gmail App Password**

1. Go to https://myaccount.google.com/security and turn on **2-Step Verification** if it is off.
2. Open https://myaccount.google.com/apppasswords
3. Name it `hmac-lab` and click Create.
4. Copy the 16-character password. Spaces do not matter.

A normal Gmail password will **not** work for SMTP. This is the most common
cause of "authentication rejected".

**Create your `.env` file**

1. In VS Code, copy `.env.example` and name the copy `.env` (exactly, with the leading dot).
2. Fill in:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.address@gmail.com
SMTP_PASS=the16characterapppassword
```

`.env` holds a real password and is listed in `.gitignore`. Never upload it,
screenshot it, or include it in what you submit.

Other providers work too; change `SMTP_HOST`. Outlook uses `smtp.office365.com`
on port 587.

## Part 3 — Run locally

```
python app.py
```

Open http://127.0.0.1:5000. Press `Ctrl + C` to stop.

Quick check before deploying: open `/sender`, enter your own second email
address as the receiver, any key, any message, and press **Seal and send
email**. The email should arrive within a minute.

---

## Part 4 — Show it on a phone

You have two options. Option A is the one to use for a demo.

### Option A: a public link (recommended)

A tunnel gives your laptop a temporary public `https://` address. The phone
can then open it from any network, including mobile data, with no firewall or
router changes.

**Cloudflare Tunnel — no account needed**

1. Install it. In PowerShell or Command Prompt:
   ```
   winget install --id Cloudflare.cloudflared
   ```
   Then close and reopen the terminal.
2. Keep `python app.py` running in one terminal.
3. Open a **second** terminal (the `+` in the VS Code terminal panel) and run:
   ```
   cloudflared tunnel --url http://localhost:5000
   ```
4. After a few seconds it prints a line containing an address like
   `https://random-words.trycloudflare.com`. That is your public link.
5. Type or message that link to your phone and open it.

**Alternative: ngrok** (free account required)

```
ngrok config add-authtoken YOUR_TOKEN
ngrok http 5000
```

Use the `https://...ngrok-free.app` address it shows. ngrok may show a
"Visit Site" warning page on first open; tap through it.

The link changes every time you restart the tunnel, so start it shortly
before your demo and open it on the phone to check.

**When you are finished, stop the tunnel** (`Ctrl + C`). While it is running,
anyone holding the link can use the sender page to send email from your
account. Do not post the link publicly.

### Option B: same Wi-Fi only

1. Phone and laptop on the same Wi-Fi.
2. On the laptop run `ipconfig` and note the **IPv4 Address**, such as `192.168.1.23`.
3. On the phone open `http://192.168.1.23:5000`.
4. If it will not load, Windows Firewall is blocking port 5000. When Windows
   asked about Python the first time, "Allow" on **Private networks** is
   needed. Some college and public Wi-Fi networks also block devices from
   talking to each other, in which case use Option A.

---

## Part 5 — Demo script

Use two devices: the laptop as the sender, the phone as the receiver (or the
other way round). Open the same site on both.

1. **Agree the key.** Say it aloud: `class-demo-key`. This is the out-of-band step.
2. **Laptop, `/sender`.** Enter the phone owner's email, key `class-demo-key`,
   message `Transfer 5000 to account 12345`. Press **Seal and send email**.
   Point out the construction panel showing how the MAC was built.
3. **Phone.** Open the email in the mail app. Select the whole body and copy it.
4. **Phone, `/receiver`.** Enter the key, paste the email, press **Extract**,
   then **Verify**. Result: **Authentic**.
5. **Be the attacker.** Change `5000` to `9000` in the Message box and verify
   again. Result: **Not authentic**, with both MACs shown side by side.
6. **Wrong key.** Restore the message, change the key, verify. **Not authentic**.

Point to make: the attacker could read and edit the email freely, but could not
produce a matching MAC without the key.

---

## How it works

`hmac_core.py` holds the algorithm, unchanged from the first version:

```
HMAC(K, m) = H( (K' xor opad) || H( (K' xor ipad) || m ) )
```

`email_service.py` formats the email and sends it with `smtplib`. The body
wraps the message in `-----BEGIN MESSAGE-----` / `-----END MESSAGE-----`
markers with the MAC on its own line, so the receiver page can pull both out
of a pasted copy.

`app.py` serves the pages and the JSON API:

| Endpoint | Purpose |
|---|---|
| `POST /api/send` | seal a message and email it |
| `POST /api/parse-email` | extract message and MAC from a pasted email |
| `POST /api/verify` | recompute and compare in constant time |
| `POST /api/generate` | MAC with full trace (used by `/lab`) |
| `GET /api/random-key` | a random 256-bit key |

## Project structure

```
hmac-sha256-lab/
├── hmac_core.py       HMAC algorithm (RFC 2104)
├── email_service.py   email formatting, parsing and SMTP sending
├── app.py             Flask backend
├── test_hmac.py       RFC 4231 test vectors
├── test_email.py      email format round-trip tests
├── test_flow.py       end-to-end sender -> receiver test
├── requirements.txt
├── .env.example       template for your SMTP settings
└── static/
    ├── home.html  sender.html + sender.js  receiver.html + receiver.js
    ├── lab.html + app.js
    └── style.css
```

## Honest limitations

- The server sends mail from **your** account and sees the key in each request.
  Over the tunnel that traffic is HTTPS, but a real design would never send a
  shared key to a third-party server. The receiver page here does it for
  demonstration convenience.
- Pasting the email into the receiver page is a manual step. Reading the
  receiver's inbox automatically would need their mailbox credentials, which
  this project deliberately avoids holding.
- Flask's built-in server suits a demo, not production.
- HMAC gives integrity and authentication between holders of the key. It does
  not hide the message, and it cannot prove to a third party which of the two
  parties made a tag.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Email is not configured" | `.env` is missing or misnamed. It must be `.env`, not `.env.txt`. Restart `python app.py` after editing it |
| "mail server rejected the sender's login" | Use a Gmail **App Password**, not your normal password |
| Email sent but not in inbox | Check Spam. Gmail may also place it in Promotions |
| Phone cannot open the link | Check the tunnel terminal is still running; copy the link exactly; try Option B on same Wi-Fi |
| `Address already in use` | Port 5000 is taken. Change `port=5000` in `app.py` and in the tunnel command |
| Verify says Not authentic on an untouched email | Keys differ (watch for a trailing space), or the message was edited |
