# Email Plugin Guide

Email-specific patterns and pitfalls discovered while building the official Email plugin.

## Setup flow

Recommended sequence for setting up the Email plugin:

1. **Get app password** → if using Gmail/Yandex/Mail.ru, generate an app-specific password (regular password won't work with IMAP)
2. **Configure IMAP** → enter server (`imap.gmail.com`) and port (993)
3. **Configure SMTP** → enter server (`smtp.gmail.com`) and port (587)
4. **Test connection** → calls IMAP login + SMTP login; confirms credentials work
5. **Poll once** → fetches unseen messages; creates contacts and messages in the system
6. **Start daemon** → continuous polling loop
7. **Test** → send an email to the configured inbox → verify it appears in /messages

## IMAP: handle folders beyond INBOX

Users may want to watch specific IMAP folders (subfolders like `INBOX.Orders`, `INBOX.Support`). The IMAP `LIST` command discovers available folders:

```python
def list_folders(self) -> list[str]:
    typ, folders = self.conn.list()
    return [parse_folder(f) for f in folders]
```

The `SELECT` command activates a folder before searching:

```python
def select_folder(self, folder: str = "INBOX") -> None:
    typ, data = self.conn.select(folder)
    if typ != "OK":
        raise ConnectionError(f"Cannot select folder {folder}")
```

## IMAP: search strategies

Two approaches — choose based on reliability needs:

| Strategy | Pros | Cons |
|---|---|---|
| `SEARCH UNSEEN` | Returns only unread messages, built-in flag | May miss messages if another client marks as seen |
| `SEARCH SINCE {date}` | Reliable even if messages are marked read | Returns duplicates on repeated runs |
| Both combined | Best reliability | Slightly more complex |

The Email plugin uses `UNSEEN` by default with `mark_as_seen` option.

## IMAP: fetch only what you need

IMAP `FETCH` can request specific parts — don't fetch the entire message unless needed:

```python
# Efficient — fetches envelope + body text only
typ, data = conn.uid("FETCH", uid, "(BODY.PEEK[TEXT])")

# Full fetch — only when debugging
typ, data = conn.uid("FETCH", uid, "(RFC822)")
```

`BODY.PEEK` vs `BODY`: `PEEK` doesn't mark the message as seen.

## SMTP: STARTTLS vs SSL

Two encryption modes for SMTP:

```python
# Port 587 — STARTTLS (upgrade after connect)
with smtplib.SMTP(smtp_host, 587) as server:
    server.starttls()
    server.login(user, password)
    server.send_message(msg)

# Port 465 — SSL from the start
with smtplib.SMTP_SSL(smtp_host, 465) as server:
    server.login(user, password)
    server.send_message(msg)
```

The Email plugin uses port 587 + STARTTLS by default (most compatible).

## Subject vs reply threading

When replying to an email, preserve the subject with "Re:" prefix:

```python
def reply_subject(original: str) -> str:
    """Add 'Re:' prefix if not already present."""
    prefix = "Re: "
    if original.startswith(prefix):
        return original
    # Some clients use "RE:", "re:", etc.
    if original.lower().startswith("re:"):
        return original
    return prefix + original
```

## Config: reload each cycle

Same pattern as Telegram — load config fresh inside the polling loop:

```python
while not stop:
    config = JsonConfigManager().load()
    email_cfg = config.email  # raises if not configured
    # ... poll IMAP ...
    time.sleep(email_cfg.poll_interval_seconds)
```

## No external dependencies

The Email plugin uses **only stdlib** — no `pip install` needed:

| Module | Usage |
|---|---|
| `imaplib` | IMAP protocol (receive) |
| `smtplib` | SMTP protocol (send) |
| `email` | Parse RFC822 messages |
| `email.policy` | Default message policy |
| `email.mime.text` | Build MIMEText messages |
| `email.parser` | Parse raw bytes → email object |
| `ssl` | TLS context for IMAP/SMTP |

This is intentional — email protocols haven't changed in decades, stdlib handles them well.

## Config: no AppConfig field

Email config does NOT live in `AppConfig`. It uses its own key in `data/config.json`:

```json
{
  "general": { ... },
  "llm": { ... },
  "telegram": { ... },
  "email": {
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "imap_ssl": true,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_ssl": true,
    "email_address": "my@email.com",
    "email_password": "<encrypted>",
    "poll_interval_seconds": 60,
    "folder": "INBOX",
    "mark_as_seen": true
  }
}
```

The password is encrypted via Fernet (same mechanism as Telegram token).

## Known pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Using regular Gmail password | IMAP login fails with "Invalid credentials" | Generate app-specific password |
| IMAP folder doesn't exist | `SELECT` fails with error | Validate folder exists before using |
| Message with no plain text part | `body` is empty | Fallback: extract text from first `text/*` part |
| Large mailbox | `SEARCH UNSEEN` is slow | Add SEARCH SINCE filter: `SEARCH UNSEEN SINCE 01-Jan-2026` |
| Connection timeout on IMAP | Daemon hangs | Set `timeout` parameter on IMAP4_SSL |
| UTF-8 subjects from some clients | Subject is garbled | Decode with `email.header.decode_header()` |
