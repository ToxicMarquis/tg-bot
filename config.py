from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: tuple[int, ...]
    timezone: str
    api_base_url: str | None
    db_path: str


def _parse_admin_ids(raw: str) -> tuple[int, ...]:
    admin_ids = []
    for chunk in raw.replace(";", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            admin_ids.append(int(chunk))
        except ValueError as error:
            raise ConfigError(
                f"ADMIN_ID содержит некорректное значение: {chunk!r}. "
                "Ожидается числовой Telegram ID (можно несколько через запятую)."
            ) from error
    return tuple(admin_ids)


def _parse_api_base_url(raw: str) -> str | None:
    url = raw.strip().rstrip("/")
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        raise ConfigError(
            f"TELEGRAM_API_URL должен начинаться с http:// или https://, получено: {raw!r}"
        )
    return url


def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ConfigError(
            "Не задан BOT_TOKEN. Скопируйте .env.example в .env "
            "и укажите токен, полученный у @BotFather."
        )
    admin_ids = _parse_admin_ids(os.getenv("ADMIN_ID", ""))
    if not admin_ids:
        raise ConfigError(
            "Не задан ADMIN_ID. Укажите Telegram ID администратора, "
            "которому будут приходить заявки (узнать можно у @userinfobot)."
        )
    timezone = os.getenv("TIMEZONE", "Europe/Moscow").strip() or "Europe/Moscow"
    api_base_url = _parse_api_base_url(os.getenv("TELEGRAM_API_URL", ""))
    db_path = os.getenv("DB_PATH", "bot.db").strip() or "bot.db"
    return Config(
        bot_token=bot_token,
        admin_ids=admin_ids,
        timezone=timezone,
        api_base_url=api_base_url,
        db_path=db_path,
    )
