# Telegram Plugin

Telegram bot integration for ai-mini-box — poll messages from chats and save them as contacts/messages.

## Install

```bash
pip install ai-mini-box-telegram
```

## Get a bot token

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot` and follow the instructions
3. Copy the token you receive

## Configure

```bash
ai-mini-box config set telegram_token "your_token_here"
ai-mini-box config set telegram_allowed_chat_ids "[123456789]"
```

Or set the token via the web interface: Plugins → telegram → token field.

## Allowed chats

By default the bot ignores messages from all chats. Add chat IDs to `telegram_allowed_chat_ids` (comma-separated) to allow specific chats.
