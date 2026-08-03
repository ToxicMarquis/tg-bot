from __future__ import annotations
import logging
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)
WEEKDAYS = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
_SLOT_RE = re.compile(
    r"^(\d{1,2})[.\-/](\d{1,2})(?:[.\-/](\d{2,4}))?[\s,]+(\d{1,2})[:.](\d{2})$"
)
_tz: ZoneInfo | timezone = ZoneInfo("Europe/Moscow")


def configure(tz_name: str) -> None:
    global _tz
    try:
        _tz = ZoneInfo(tz_name)
    except Exception:
        logger.warning("Неизвестный часовой пояс %r, использую UTC", tz_name)
        _tz = timezone.utc


def get_timezone() -> ZoneInfo | timezone:
    return _tz


def now() -> datetime:
    return datetime.now(_tz).replace(tzinfo=None, microsecond=0)


def localize(value: datetime) -> datetime:
    return value.replace(tzinfo=_tz)


def to_iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S")


def from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def format_slot(value: datetime) -> str:
    return f"{value:%d.%m} ({WEEKDAYS[value.weekday()]}) {value:%H:%M}"


def format_datetime(value: datetime) -> str:
    return f"{value:%d.%m.%Y %H:%M}"


def parse_slot(text: str) -> datetime | None:
    match = _SLOT_RE.match(text.strip())
    if match is None:
        return None
    day, month, year, hour, minute = match.groups()
    current = now()
    if year is None:
        year_value = current.year
    else:
        year_value = int(year)
        if year_value < 100:
            year_value += 2000
    try:
        value = datetime(year_value, int(month), int(day), int(hour), int(minute))
    except ValueError:
        return None
    if year is None and value < current:
        try:
            value = value.replace(year=year_value + 1)
        except ValueError:
            return None
    return value
