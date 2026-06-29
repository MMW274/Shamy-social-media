"""Pipeline configuration loaded from environment."""
from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


REQUIRED = [
    "GEMINI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID_SNEHA",
    "TELEGRAM_CHAT_ID_MEHUL",
    "DRIVE_ROOT_FOLDER_ID",
]


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    telegram_bot_token: str
    telegram_chat_id_sneha: int
    telegram_chat_id_mehul: int
    drive_root_folder_id: str
    google_credentials_json: str
    vizard_api_key: str
    timezone: str
    dry_run: bool
    log_level: str


def load_settings() -> Settings:
    load_dotenv()
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")

    return Settings(
        gemini_api_key=os.environ["GEMINI_API_KEY"],
        telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        telegram_chat_id_sneha=int(os.environ["TELEGRAM_CHAT_ID_SNEHA"]),
        telegram_chat_id_mehul=int(os.environ["TELEGRAM_CHAT_ID_MEHUL"]),
        drive_root_folder_id=os.environ["DRIVE_ROOT_FOLDER_ID"],
        google_credentials_json=os.getenv("GOOGLE_CREDENTIALS_JSON", ""),
        vizard_api_key=os.getenv("VIZARD_API_KEY", ""),
        timezone=os.getenv("TZ", "Europe/Berlin"),
        dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
