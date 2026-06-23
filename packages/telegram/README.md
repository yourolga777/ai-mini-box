# ai-mini-box-telegram

Telegram Bot API integration for ai-mini-box. Receives messages via long polling and saves them to the database.

## Installation

```bash
pip install ai-mini-box-telegram
```

Requires `ai-mini-box-core>=5.0.0`.

## Setup

Set your Telegram bot token (get one from [@BotFather](https://t.me/botfather)):

```bash
ai-mini-box config set telegram_token "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
```

Optionally restrict which chats the bot processes:

```bash
ai-mini-box config set telegram_allowed_chat_ids "[123456789, 987654321]"
```

## Usage

### Poll once

Fetch new messages and save them:

```bash
ai-mini-box telegram poll
# → Processed 3 new messages
```

### Run daemon

Continuous polling loop (Ctrl+C to stop):

```bash
ai-mini-box telegram daemon
```

Configuration fields used:

| Field | Default | Description |
|---|---|---|
| `telegram_token` | — | Bot token (required, encrypted) |
| `telegram_allowed_chat_ids` | `[]` | Restrict to specific chats (empty = all) |
| `poll_interval` | `30` | Seconds between polls in daemon mode |
