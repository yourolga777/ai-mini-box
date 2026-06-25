import base64
import json
import os
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


SENSITIVE_FIELDS = frozenset({
    "email_password", "telegram_token", "whatsapp_api_key",
    "sms_api_key", "sms_api_secret", "yookassa_secret_key",
    "tinkoff_password", "sber_password",
})


def _derive_key(secret: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


class AppConfig(BaseModel):
    telegram_token: str = ""
    telegram_bot_name: str = ""
    telegram_bot_username: str = ""
    telegram_allowed_chat_ids: list[int] = Field(default_factory=list)
    email_imap_server: str = "imap.yandex.ru"
    email_imap_port: int = 993
    email_login: str = ""
    email_password: str = ""
    llm_model_path: str = "models/Phi-3-mini-q4.gguf"
    llm_n_ctx: int = 4096
    llm_n_threads: int = 4
    poll_interval: int = 30
    auto_backup_interval: int = 0
    work_schedule_start: str = "09:00"
    work_schedule_end: str = "18:00"
    whatsapp_api_key: str = ""
    whatsapp_phone: str = ""
    notification_on_order: bool = True
    notification_on_complaint: bool = True
    notification_on_error: bool = True
    sms_provider: str = ""
    sms_api_key: str = ""
    sms_api_secret: str = ""
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    tinkoff_terminal_key: str = ""
    tinkoff_password: str = ""
    sber_merchant_id: str = ""
    sber_login: str = ""
    sber_password: str = ""

    class Config:
        env_prefix = "AI_BOX_"

    @classmethod
    def guess_section(cls, key: str) -> str:
        prefix = key.split("_")[0]
        section_map = {
            "telegram": "Telegram", "email": "Email", "llm": "LLM",
            "poll": "General", "auto": "General", "work": "Schedule",
            "whatsapp": "WhatsApp", "notification": "Notifications",
            "sms": "SMS", "yookassa": "YooKassa", "tinkoff": "Tinkoff",
            "sber": "Sber",
        }
        return section_map.get(prefix, "General")


class JsonConfigManager:
    def __init__(self, path: str | Path = "data/config.json"):
        self.path = Path(path)
        self._fernet: Optional[Fernet] = None

    def _get_fernet(self) -> Fernet:
        if self._fernet is None:
            machine_id = os.environ.get("AI_BOX_SECRET", default="default-dev-secret")
            salt = b"ai-mini-box-salt"
            key = _derive_key(machine_id, salt)
            self._fernet = Fernet(key)
        return self._fernet

    def _encrypt(self, value: str) -> str:
        if not value:
            return value
        return self._get_fernet().encrypt(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        if not value:
            return value
        try:
            return self._get_fernet().decrypt(value.encode()).decode()
        except Exception:
            return value

    def load(self) -> AppConfig:
        config = AppConfig()
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            for key, value in data.items():
                if key in type(config).model_fields:
                    if key in SENSITIVE_FIELDS and isinstance(value, str):
                        value = self._decrypt(value)
                    setattr(config, key, value)
        self._apply_env_overrides(config)
        return config

    def _apply_env_overrides(self, config: AppConfig):
        prefix = "AI_BOX_"
        for field_name in AppConfig.model_fields:
            env_key = f"{prefix}{field_name.upper()}"
            env_value = os.environ.get(env_key)
            if env_value is not None:
                field_type = config.model_fields[field_name].annotation
                if field_type is int:
                    env_value = int(env_value)
                elif field_type is bool:
                    env_value = env_value.lower() in ("1", "true", "yes")
                setattr(config, field_name, env_value)

    def save(self, config: AppConfig):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = config.model_dump()
        for key in SENSITIVE_FIELDS:
            if key in data and data[key]:
                data[key] = self._encrypt(data[key])
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def set(self, key: str, value: Any) -> bool:
        if key not in AppConfig.model_fields:
            raise ValueError(f"Unknown config key: {key}")

        field_info = AppConfig.model_fields[key]
        field_type = field_info.annotation

        if field_type is int:
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValueError(f"'{key}' must be an integer, got '{value}'")
        elif field_type is bool:
            if isinstance(value, str):
                value = value.lower() in ("1", "true", "yes", "on")
            else:
                value = bool(value)
        elif field_type == list[int]:
            if isinstance(value, str):
                value = json.loads(value) if value.startswith("[") else [int(x.strip()) for x in value.split(",") if x.strip()]
            value = [int(x) for x in value]

        current = self.load()
        raw = current.model_dump()
        raw[key] = value
        try:
            new_config = AppConfig(**raw)
        except ValidationError as e:
            raise ValueError(f"Invalid value for '{key}': {e.errors()[0]['msg']}")

        self.save(new_config)
        return True

    def unset(self, key: str) -> bool:
        if key not in AppConfig.model_fields:
            raise ValueError(f"Unknown config key: {key}")

        if not self.path.exists():
            return False

        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)

        if key not in data:
            return False

        del data[key]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
