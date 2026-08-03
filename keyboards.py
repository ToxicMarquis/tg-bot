from __future__ import annotations
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
import timeutils
from db import Slot

BTN_CANCEL = "❌ Отменить"
BTN_SHARE_PHONE = "📱 Отправить свой номер"
BTN_CONFIRM = "✅ Отправить заявку"
BTN_RESTART = "🔄 Заполнить заново"
remove_keyboard = ReplyKeyboardRemove()


class SlotCB(CallbackData, prefix="slot"):
    action: str
    slot_id: int = 0


class AdminCB(CallbackData, prefix="adm"):
    action: str
    slot_id: int = 0


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
        input_field_placeholder="Введите ответ или нажмите «Отменить»",
    )


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_SHARE_PHONE, request_contact=True)],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Например: +7 999 123-45-67",
    )


def confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CONFIRM)],
            [KeyboardButton(text=BTN_RESTART), KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Всё верно?",
    )


def slots_keyboard(slots: list[Slot]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        builder.button(
            text=timeutils.format_slot(slot.starts_at),
            callback_data=SlotCB(action="pick", slot_id=slot.id),
        )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(
            text="🕓 Согласовать время по телефону",
            callback_data=SlotCB(action="any").pack(),
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить список",
            callback_data=SlotCB(action="refresh").pack(),
        )
    )
    return builder.as_markup()


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить окошки", callback_data=AdminCB(action="add"))
    builder.button(text="📅 Окошки", callback_data=AdminCB(action="slots"))
    builder.button(text="📋 Заявки", callback_data=AdminCB(action="apps"))
    builder.adjust(1, 2)
    return builder.as_markup()


def admin_slots_keyboard(slots: list[Slot]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        if slot.is_booked:
            continue
        builder.button(
            text=f"🗑 {timeutils.format_slot(slot.starts_at)}",
            callback_data=AdminCB(action="del", slot_id=slot.id),
        )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Меню", callback_data=AdminCB(action="menu").pack()
        )
    )
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Меню", callback_data=AdminCB(action="menu"))
    return builder.as_markup()
