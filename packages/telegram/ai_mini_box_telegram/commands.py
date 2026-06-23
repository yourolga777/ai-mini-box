import signal
import sys
import time

import typer
from loguru import logger

from ai_mini_box.infrastructure.config import JsonConfigManager
from ai_mini_box.infrastructure.database import get_db

from .bot import TelegramBot
from .update_checker import warn_updates
from .exceptions import TelegramAPIError
from .handlers import process_update
from .state import FileTelegramStateRepo

logger.add("logs/plugin_telegram.log", rotation="1 MB", retention=3)


def _resolve_config() -> tuple[str, list[int], int]:
    config = JsonConfigManager().load()
    token = config.telegram_token
    if not token:
        typer.echo("Error: telegram_token not set. Run: ai-mini-box config set telegram_token <token>")
        raise typer.Exit(1)
    return token, config.telegram_allowed_chat_ids, config.poll_interval


def _do_poll(bot: TelegramBot, state: FileTelegramStateRepo, allowed_chat_ids: list[int]) -> int:
    offset = state.get_offset()
    updates = bot.get_updates(offset=offset)
    count = 0
    for update in updates:
        with get_db() as session:
            if process_update(update, session, allowed_chat_ids=allowed_chat_ids):
                count += 1
                state.save_offset(update["update_id"] + 1)
    return count


def register(app: typer.Typer):
    tg = typer.Typer(help="Telegram bot integration")
    app.add_typer(tg, name="telegram")

    @tg.command()
    def poll():
        """Poll Telegram for new messages once and save them."""
        token, allowed_chat_ids, _ = _resolve_config()
        bot = TelegramBot(token)
        state = FileTelegramStateRepo()
        try:
            count = _do_poll(bot, state, allowed_chat_ids)
        except TelegramAPIError as e:
            typer.echo(f"Error: {e}")
            raise typer.Exit(1)
        typer.echo(f"Processed {count} new messages")

    @tg.command()
    def daemon():
        """Run continuous polling loop until interrupted."""
        token, allowed_chat_ids, interval = _resolve_config()
        warn_updates("ai-mini-box-core", "ai-mini-box-telegram")
        bot = TelegramBot(token)
        state = FileTelegramStateRepo()
        logger.info(f"Starting telegram daemon (poll interval={interval}s)")

        stop = False

        def _signal_handler(signum, frame):
            nonlocal stop
            stop = True
            logger.info("Shutdown requested, finishing current cycle...")

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        while not stop:
            logger.info(f"Polling... (interval={interval}s)")
            try:
                count = _do_poll(bot, state, allowed_chat_ids)
                if count:
                    logger.info(f"Processed {count} new messages")
            except TelegramAPIError as e:
                logger.error(f"Polling error: {e}")
            except Exception as e:
                logger.error(f"Unexpected polling error: {e}")
            if stop:
                break
            try:
                time.sleep(interval)
            except KeyboardInterrupt:
                stop = True

        logger.info("Telegram daemon stopped")
