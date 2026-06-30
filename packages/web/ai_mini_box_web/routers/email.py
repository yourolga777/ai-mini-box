import imaplib
import smtplib
import ssl
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_mini_box_web.services.plugin_manager import PluginManager

router = APIRouter()

CONFIG_PATH = Path("data/config.json")


class EmailTestRequest(BaseModel):
    imap_host: str
    imap_port: int = 993
    imap_ssl: bool = True
    smtp_host: str
    smtp_port: int = 587
    smtp_ssl: bool = True
    email_address: str
    email_password: str


def _test_imap(host: str, port: int, ssl_enabled: bool, user: str, password: str) -> tuple[bool, str | None]:
    try:
        if ssl_enabled:
            ctx = ssl.create_default_context()
            conn = imaplib.IMAP4_SSL(host, port, timeout=30, ssl_context=ctx)
        else:
            conn = imaplib.IMAP4(host, port, timeout=30)
        conn.login(user, password)
        conn.select("INBOX")
        conn.logout()
        return True, None
    except Exception as e:
        return False, str(e)


def _test_smtp(host: str, port: int, ssl_enabled: bool, user: str, password: str) -> tuple[bool, str | None]:
    try:
        if ssl_enabled and port == 465:
            ctx = ssl.create_default_context()
            conn = smtplib.SMTP_SSL(host, port, timeout=30, context=ctx)
        else:
            conn = smtplib.SMTP(host, port, timeout=30)
            if ssl_enabled:
                conn.starttls()
        conn.login(user, password)
        conn.quit()
        return True, None
    except Exception as e:
        return False, str(e)


def _get_email_config() -> dict | None:
    if not CONFIG_PATH.exists():
        return None
    import json
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return raw.get("email")


@router.get("/status")
def email_status():
    cfg = _get_email_config()
    if not cfg:
        return {
            "configured": False,
            "connected": False,
            "last_poll_at": None,
            "last_error": None,
            "messages_fetched_today": 0,
            "imap_host": "", "imap_port": 993, "imap_ssl": True,
            "smtp_host": "", "smtp_port": 587, "smtp_ssl": True,
            "email_address": "",
            "folder": "INBOX", "max_per_cycle": 50,
            "mark_as_seen": True, "poll_interval_seconds": 60,
        }

    pm = PluginManager()
    plugin = pm.get_plugin("email")
    daemon_running = plugin and plugin.get("status") == "running"

    try:
        from ai_mini_box.core.services.registry import get_service
        svc = get_service("email_service")
        if svc:
            live = svc.get_status()
            return {
                "configured": True,
                "connected": live.connected,
                "last_poll_at": live.last_poll_at.isoformat() if live.last_poll_at else None,
                "last_error": live.last_error,
                "messages_fetched_today": live.fetched_today,
                "imap_host": cfg.get("imap_host", ""),
                "imap_port": cfg.get("imap_port", 993),
                "imap_ssl": cfg.get("imap_ssl", True),
                "smtp_host": cfg.get("smtp_host", ""),
                "smtp_port": cfg.get("smtp_port", 587),
                "smtp_ssl": cfg.get("smtp_ssl", True),
                "email_address": cfg.get("email_address", ""),
                "folder": cfg.get("folder", "INBOX"),
                "max_per_cycle": cfg.get("max_per_cycle", 50),
                "mark_as_seen": cfg.get("mark_as_seen", True),
                "poll_interval_seconds": cfg.get("poll_interval_seconds", 60),
            }
    except (ImportError, Exception):
        pass

    return {
        "configured": True,
        "connected": daemon_running,
        "last_poll_at": None,
        "last_error": None,
        "messages_fetched_today": 0,
        "imap_host": cfg.get("imap_host", ""),
        "imap_port": cfg.get("imap_port", 993),
        "imap_ssl": cfg.get("imap_ssl", True),
        "smtp_host": cfg.get("smtp_host", ""),
        "smtp_port": cfg.get("smtp_port", 587),
        "smtp_ssl": cfg.get("smtp_ssl", True),
        "email_address": cfg.get("email_address", ""),
        "folder": cfg.get("folder", "INBOX"),
        "max_per_cycle": cfg.get("max_per_cycle", 50),
        "mark_as_seen": cfg.get("mark_as_seen", True),
        "poll_interval_seconds": cfg.get("poll_interval_seconds", 60),
    }


@router.post("/test")
def email_test(body: EmailTestRequest):
    imap_ok, imap_err = _test_imap(
        body.imap_host, body.imap_port, body.imap_ssl,
        body.email_address, body.email_password,
    )
    smtp_ok, smtp_err = _test_smtp(
        body.smtp_host, body.smtp_port, body.smtp_ssl,
        body.email_address, body.email_password,
    )

    if imap_ok and smtp_ok:
        return {"success": True, "imap": True, "smtp": True, "message": None}

    errors = []
    if imap_err:
        errors.append(f"IMAP: {imap_err}")
    if smtp_err:
        errors.append(f"SMTP: {smtp_err}")
    return {"success": False, "imap": imap_ok, "smtp": smtp_ok, "message": "; ".join(errors)}
