from __future__ import annotations
import logging
from html import escape
from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject
import texts
import timeutils
from config import Config
from db import Database
from keyboards import (
    AdminCB,
    admin_menu_keyboard,
    admin_slots_keyboard,
    back_to_menu_keyboard,
    cancel_keyboard,
    remove_keyboard,
)
from states import AdminForm

logger = logging.getLogger(__name__)
MENU_TEXT = "🛠 <b>Панель администратора</b>\n\nВыберите действие:"
ADD_HELP = (
    "➕ <b>Добавление окошек</b>\n\n"
    "Пришлите дату и время – по одному окошку в строке:\n\n"
    "<code>04.08 10:00\n"
    "04.08 14:30\n"
    "05.08.2026 09:00</code>\n\n"
    "Год можно не указывать – возьму ближайший.\n"
    "Занятые и уже добавленные окошки пропущу."
)


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject, config: Config) -> bool:
        user = getattr(event, "from_user", None)
        return user is not None and user.id in config.admin_ids


router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def _slots_text(db: Database) -> str:
    slots = await db.upcoming_slots()
    if not slots:
        return "📅 Ближайших окошек нет. Добавьте их кнопкой «Добавить окошки»."
    lines = ["📅 <b>Ближайшие окошки</b>\n"]
    for slot in slots:
        mark = "🔴 занято" if slot.is_booked else "🟢 свободно"
        lines.append(f"{timeutils.format_slot(slot.starts_at)} – {mark}")
    lines.append("\nКнопкой ниже можно удалить свободное окошко.")
    return "\n".join(lines)


@router.message(Command("admin"))
async def open_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(MENU_TEXT, reply_markup=admin_menu_keyboard())


@router.callback_query(AdminCB.filter(F.action == "menu"))
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(MENU_TEXT, reply_markup=admin_menu_keyboard())
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "add"))
async def ask_slots(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminForm.add_slots)
    await callback.message.edit_text(ADD_HELP)
    await callback.message.answer(
        "Жду список окошек 👇", reply_markup=cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminForm.add_slots, F.text)
async def save_slots(message: Message, state: FSMContext, db: Database) -> None:
    moments = []
    errors = []
    for line in message.text.splitlines():
        line = line.strip()
        if not line:
            continue
        moment = timeutils.parse_slot(line)
        if moment is None:
            errors.append(line)
        elif moment <= timeutils.now():
            errors.append(f"{line} (уже прошло)")
        else:
            moments.append(moment)
    added = await db.add_slots(moments) if moments else 0
    report = []
    if added:
        report.append(f"✅ Добавлено окошек: <b>{added}</b>")
    if len(moments) > added:
        report.append(f"⚠️ Уже были в списке: {len(moments) - added}")
    if errors:
        listed = "\n".join(f"• {escape(line)}" for line in errors[:10])
        report.append(f"❌ Не понял строки:\n{listed}")
    if not report:
        report.append("Не нашёл ни одного окошка в сообщении.")
    await state.clear()
    await message.answer("\n\n".join(report), reply_markup=remove_keyboard)
    slots = await db.upcoming_slots()
    await message.answer(await _slots_text(db), reply_markup=admin_slots_keyboard(slots))


@router.message(AdminForm.add_slots)
async def save_slots_wrong_type(message: Message) -> None:
    await message.answer("Нужен текст со списком дат 🙂", reply_markup=cancel_keyboard())


@router.callback_query(AdminCB.filter(F.action == "slots"))
async def show_slots(callback: CallbackQuery, db: Database) -> None:
    slots = await db.upcoming_slots()
    await callback.message.edit_text(
        await _slots_text(db), reply_markup=admin_slots_keyboard(slots)
    )
    await callback.answer()


@router.callback_query(AdminCB.filter(F.action == "del"))
async def delete_slot(
    callback: CallbackQuery, callback_data: AdminCB, db: Database
) -> None:
    deleted = await db.delete_free_slot(callback_data.slot_id)
    slots = await db.upcoming_slots()
    try:
        await callback.message.edit_text(
            await _slots_text(db), reply_markup=admin_slots_keyboard(slots)
        )
    except TelegramAPIError:
        pass
    await callback.answer("Окошко удалено" if deleted else "Окошко уже занято")


@router.callback_query(AdminCB.filter(F.action == "apps"))
async def show_applications(callback: CallbackQuery, db: Database) -> None:
    applications = await db.recent_applications()
    if applications:
        lines = ["📋 <b>Последние заявки</b>\n"]
        lines += [texts.application_line(item) for item in applications]
        text = "\n\n".join(lines)
    else:
        text = "📋 Заявок пока нет."
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard())
    await callback.answer()
