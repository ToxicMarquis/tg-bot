from __future__ import annotations
from html import escape
import timeutils
from db import Application

NO_SLOT = "по договорённости"


def user_link(user_id: int, full_name: str, username: str | None) -> str:
    parts = [f'<a href="tg://user?id={user_id}">{escape(full_name)}</a>']
    if username:
        parts.append(f"@{username}")
    parts.append(f"(ID: <code>{user_id}</code>)")
    return " ".join(parts)


def slot_text(starts_at) -> str:
    return timeutils.format_datetime(starts_at) if starts_at else NO_SLOT


def preview(address: str, phone: str, service: str, starts_at) -> str:
    return (
        "<b>Проверьте заявку</b>\n\n"
        f"🏠 <b>Адрес:</b> {escape(address)}\n"
        f"📞 <b>Телефон:</b> {escape(phone)}\n"
        f"🔧 <b>Вид работ:</b> {escape(service)}\n"
        f"🕒 <b>Время:</b> {slot_text(starts_at)}\n\n"
        "Всё верно?"
    )


def application_card(application: Application, title: str) -> str:
    return (
        f"{title}\n\n"
        f"🏠 <b>Адрес:</b> {escape(application.address)}\n"
        f"📞 <b>Телефон:</b> {escape(application.phone)}\n"
        f"🔧 <b>Вид работ:</b> {escape(application.service)}\n"
        f"🕒 <b>Время:</b> {slot_text(application.starts_at)}\n\n"
        f"👤 <b>Клиент:</b> "
        f"{user_link(application.user_id, application.full_name, application.username)}\n"
        f"📨 <b>Оставлена:</b> {timeutils.format_datetime(application.created_at)}"
    )


def new_application(application: Application) -> str:
    return application_card(application, "🔔 <b>Новая заявка</b>")


def reminder(application: Application) -> str:
    return application_card(application, "⏰ <b>Напоминание: заявка завтра</b>")


def application_line(application: Application) -> str:
    return (
        f"<b>#{application.id}</b> · {slot_text(application.starts_at)}\n"
        f"🏠 {escape(application.address)}\n"
        f"📞 {escape(application.phone)} · 🔧 {escape(application.service)}"
    )
