from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(Exception):
    pass


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"Required environment variable {name} is not set")
    return value


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    openrouter_api_key: str
    openrouter_model: str
    rate_limit_per_minute: int
    database_path: str

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            telegram_bot_token=_require_env("TELEGRAM_BOT_TOKEN"),
            openrouter_api_key=_require_env("OPENROUTER_API_KEY"),
            openrouter_model=os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001"),
            rate_limit_per_minute=int(os.environ.get("RATE_LIMIT_PER_MINUTE", "10")),
            database_path=os.environ.get("DATABASE_PATH", "data/bot.db"),
        )
