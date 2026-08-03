from __future__ import annotations
import re

ADDRESS_MIN_LENGTH = 5
ADDRESS_MAX_LENGTH = 200
SERVICE_MIN_LENGTH = 3
SERVICE_MAX_LENGTH = 300
PHONE_MIN_DIGITS = 10
PHONE_MAX_DIGITS = 15
_PHONE_ALLOWED_RE = re.compile(r"^[\d\s()+\-.]+$")


def clean_text(value: str) -> str:
    return " ".join(value.split())


def validate_address(value: str) -> str | None:
    address = clean_text(value)
    if not ADDRESS_MIN_LENGTH <= len(address) <= ADDRESS_MAX_LENGTH:
        return None
    return address


def validate_service(value: str) -> str | None:
    service = clean_text(value)
    if not SERVICE_MIN_LENGTH <= len(service) <= SERVICE_MAX_LENGTH:
        return None
    return service


def validate_phone(value: str) -> str | None:
    raw = value.strip()
    if not raw or not _PHONE_ALLOWED_RE.match(raw):
        return None
    digits = re.sub(r"\D", "", raw)
    if not PHONE_MIN_DIGITS <= len(digits) <= PHONE_MAX_DIGITS:
        return None
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == PHONE_MIN_DIGITS:
        return digits
    return "+" + digits
