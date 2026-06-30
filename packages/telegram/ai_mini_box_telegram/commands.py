import json
import signal
import time

import typer
from loguru import logger

from ai_mini_box.core.services.registry import register_service
from ai_mini_box.infrastructure.config import JsonConfigManager
from ai_mini_box.infrastructure.database import get_db

from .bot import TelegramBot, TelegramService
from .config import TelegramPluginConfig
from .update_checker import warn_updates
from .exceptions import TelegramAPIError
from .handlers import process_update
from .state import FileTelegramStateRepo

logger.add("logs/plugin_telegram.log", rotation="1 MB", retention=3)


def config_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "api_base_url": {"type": "string", "title": "Базовый URL API Telegram", "format": "uri", "default": "https://api.telegram.org/bot"},
            "request_timeout": {"type": "integer", "title": "Таймаут запроса (сек)", "default": 10},
            "poll_interval": {"type": "integer", "title": "Интервал опроса (сек)", "default": 30},
        },
    }


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
    register_service("telegram", TelegramService())
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

    cfg_typer = typer.Typer(help="View and change telegram plugin config")
    tg.add_typer(cfg_typer, name="config")

    @cfg_typer.command()
    def show():
        """Show current telegram plugin configuration."""
        cfg = TelegramPluginConfig()
        data = cfg.all()
        data["telegram_token"] = "***" if JsonConfigManager().load().telegram_token else "(not set)"
        typer.echo(json.dumps(data, indent=2))

    @cfg_typer.command()
    def set(key: str = typer.Argument(help="Config key"), value: str = typer.Argument(help="Config value")):
        """Set a config value (api_base_url, request_timeout, poll_interval)."""
        allowed = {"api_base_url", "request_timeout", "poll_interval"}
        if key not in allowed:
            typer.echo(f"Unknown key '{key}'. Allowed: {', '.join(sorted(allowed))}")
            raise typer.Exit(1)
        if key in ("request_timeout", "poll_interval"):
            try:
                value = int(value)
            except ValueError:
                typer.echo(f"'{key}' must be an integer")
                raise typer.Exit(1)
        if key == "poll_interval":
            JsonConfigManager().set(key, value)
        else:
            TelegramPluginConfig().set(key, value)
        typer.echo(f"telegram.{key} = {value}")

    @tg.command()
    def daemon():
        """Run continuous polling loop until interrupted."""
        warn_updates("ai-mini-box-core", "ai-mini-box-telegram")
        state = FileTelegramStateRepo()

        stop = False

        def _signal_handler(signum, frame):
            nonlocal stop
            stop = True
            logger.info("Shutdown requested, finishing current cycle...")

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        bot = None
        while not stop:
            try:
                token, allowed_chat_ids, interval = _resolve_config()
            except typer.Exit:
                logger.error("telegram_token not set — daemon waiting...")
                try:
                    time.sleep(30)
                except KeyboardInterrupt:
                    stop = True
                continue

            if bot is None or bot.token != token:
                bot = TelegramBot(token)
                logger.info("Telegram bot initialized with updated token")

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
