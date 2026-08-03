from __future__ import annotations
import logging
from html import escape
from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
import texts
import timeutils
from config import Config
from db import Application, Database
from keyboards import (
    BTN_CONFIRM,
    BTN_RESTART,
    SlotCB,
    cancel_keyboard,
    confirm_keyboard,
    phone_keyboard,
    remove_keyboard,
    slots_keyboard,
)
from reminders import ReminderService
from states import ApplicationForm
from validators import (
    ADDRESS_MAX_LENGTH,
    ADDRESS_MIN_LENGTH,
    SERVICE_MAX_LENGTH,
    SERVICE_MIN_LENGTH,
    validate_address,
    validate_phone,
    validate_service,
)

logger = logging.getLogger(__name__)
router = Router(name="application")


async def _notify_admins(bot: Bot, config: Config, application: Application) -> int:
    delivered = 0
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, texts.new_application(application))
        except TelegramAPIError as error:
            logger.error("Не удалось отправить заявку админу %s: %s", admin_id, error)
        else:
            delivered += 1
    return delivered


async def _ask_address(message: Message, state: FSMContext) -> None:
    await state.set_state(ApplicationForm.address)
    await message.answer(
        "Шаг 1 из 4.\n"
        "🏠 Напишите <b>адрес</b>, куда нужно приехать.\n\n"
        "Например: <i>г. Москва, ул. Ленина, д. 10, кв. 5</i>",
        reply_markup=cancel_keyboard(),
    )


async def _ask_slot(message: Message, state: FSMContext, db: Database) -> None:
    await state.set_state(ApplicationForm.slot)
    slots = await db.free_slots()
    if slots:
        text = (
            "Шаг 4 из 4.\n"
            "🕒 Выберите удобное <b>время</b> из свободных окошек:"
        )
    else:
        text = (
            "Шаг 4 из 4.\n"
            "🕒 Свободных окошек сейчас нет.\n"
            "Можно оставить заявку без времени – мастер позвонит и согласует его."
        )
    await message.answer(text, reply_markup=slots_keyboard(slots))


async def _show_preview(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    starts_at = data.get("slot_starts_at")
    await state.set_state(ApplicationForm.confirm)
    await message.answer(
        texts.preview(
            data["address"],
            data["phone"],
            data["service"],
            timeutils.from_iso(starts_at) if starts_at else None,
        ),
        reply_markup=confirm_keyboard(),
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"Здравствуйте, {escape(message.from_user.first_name)}! 👋\n\n"
        "Я помогу оставить заявку на услугу – это займёт меньше минуты.\n"
        "Спрошу адрес, телефон, вид работ и удобное время.\n\n"
        "Если передумаете, нажмите «Отменить» или отправьте /cancel."
    )
    await _ask_address(message, state)


@router.message(ApplicationForm.address, F.text)
async def process_address(message: Message, state: FSMContext) -> None:
    address = validate_address(message.text)
    if address is None:
        await message.answer(
            "Кажется, адрес указан не полностью 🤔\n"
            f"Введите от {ADDRESS_MIN_LENGTH} до {ADDRESS_MAX_LENGTH} символов – "
            "город, улицу, дом и квартиру.",
            reply_markup=cancel_keyboard(),
        )
        return
    await state.update_data(address=address)
    await state.set_state(ApplicationForm.phone)
    await message.answer(
        "Принято ✅\n\n"
        "Шаг 2 из 4.\n"
        "📞 Укажите <b>номер телефона</b> для связи.\n\n"
        "Например: <i>+7 999 123-45-67</i>\n"
        "Или нажмите кнопку ниже, чтобы отправить свой номер.",
        reply_markup=phone_keyboard(),
    )


@router.message(ApplicationForm.address)
async def process_address_wrong_type(message: Message) -> None:
    await message.answer(
        "Мне нужен адрес <b>текстом</b> 🙂\n"
        "Например: <i>г. Москва, ул. Ленина, д. 10, кв. 5</i>",
        reply_markup=cancel_keyboard(),
    )


async def _save_phone_and_ask_service(
    message: Message, state: FSMContext, phone: str
) -> None:
    await state.update_data(phone=phone)
    await state.set_state(ApplicationForm.service)
    await message.answer(
        f"Записал номер: <b>{escape(phone)}</b> ✅\n\n"
        "Шаг 3 из 4.\n"
        "🔧 Опишите <b>вид работ или услугу</b>.\n\n"
        "Например: <i>заменить смеситель на кухне</i>",
        reply_markup=cancel_keyboard(),
    )


@router.message(ApplicationForm.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext) -> None:
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer(
            "Это контакт другого человека 🤔\n"
            "Отправьте, пожалуйста, свой номер или введите его вручную.",
            reply_markup=phone_keyboard(),
        )
        return
    phone = validate_phone(contact.phone_number) or contact.phone_number
    await _save_phone_and_ask_service(message, state, phone)


@router.message(ApplicationForm.phone, F.text)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = validate_phone(message.text)
    if phone is None:
        await message.answer(
            "Не похоже на номер телефона 🤔\n"
            "Введите его цифрами, например: <i>+7 999 123-45-67</i>",
            reply_markup=phone_keyboard(),
        )
        return
    await _save_phone_and_ask_service(message, state, phone)


@router.message(ApplicationForm.phone)
async def process_phone_wrong_type(message: Message) -> None:
    await message.answer(
        "Мне нужен номер телефона 📞\n"
        "Введите его текстом или нажмите кнопку «Отправить свой номер».",
        reply_markup=phone_keyboard(),
    )


@router.message(ApplicationForm.service, F.text)
async def process_service(message: Message, state: FSMContext, db: Database) -> None:
    service = validate_service(message.text)
    if service is None:
        await message.answer(
            "Опишите задачу чуть подробнее 🙂\n"
            f"Нужно от {SERVICE_MIN_LENGTH} до {SERVICE_MAX_LENGTH} символов.\n"
            "Например: <i>установить розетку в спальне</i>",
            reply_markup=cancel_keyboard(),
        )
        return
    await state.update_data(service=service)
    await _ask_slot(message, state, db)


@router.message(ApplicationForm.service)
async def process_service_wrong_type(message: Message) -> None:
    await message.answer(
        "Опишите вид работ <b>текстом</b> 🙂\n"
        "Например: <i>заменить смеситель на кухне</i>",
        reply_markup=cancel_keyboard(),
    )


@router.callback_query(ApplicationForm.slot, SlotCB.filter(F.action == "refresh"))
async def refresh_slots(callback: CallbackQuery, db: Database) -> None:
    slots = await db.free_slots()
    try:
        await callback.message.edit_reply_markup(reply_markup=slots_keyboard(slots))
    except TelegramAPIError:
        pass
    await callback.answer("Список обновлён")


@router.callback_query(ApplicationForm.slot, SlotCB.filter(F.action == "any"))
async def pick_any_time(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(slot_id=None, slot_starts_at=None)
    await callback.message.edit_text("🕒 Время: <b>согласуем по телефону</b>")
    await callback.answer()
    await _show_preview(callback.message, state)


@router.callback_query(ApplicationForm.slot, SlotCB.filter(F.action == "pick"))
async def pick_slot(
    callback: CallbackQuery, callback_data: SlotCB, state: FSMContext, db: Database
) -> None:
    slot = await db.get_slot(callback_data.slot_id)
    if slot is None or slot.is_booked:
        slots = await db.free_slots()
        await callback.message.edit_reply_markup(reply_markup=slots_keyboard(slots))
        await callback.answer("Это окошко уже заняли, выберите другое", show_alert=True)
        return
    await state.update_data(
        slot_id=slot.id, slot_starts_at=timeutils.to_iso(slot.starts_at)
    )
    await callback.message.edit_text(
        f"🕒 Время: <b>{timeutils.format_slot(slot.starts_at)}</b>"
    )
    await callback.answer()
    await _show_preview(callback.message, state)


@router.message(ApplicationForm.slot)
async def slot_wrong_input(message: Message) -> None:
    await message.answer("Выберите время кнопкой из списка выше 👆")


@router.message(ApplicationForm.confirm, F.text == BTN_CONFIRM)
async def confirm_application(
    message: Message,
    state: FSMContext,
    bot: Bot,
    config: Config,
    db: Database,
    reminders: ReminderService,
) -> None:
    data = await state.get_data()
    application = await db.create_application(
        slot_id=data.get("slot_id"),
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        address=data["address"],
        phone=data["phone"],
        service=data["service"],
    )
    if application is None:
        await message.answer(
            "Пока вы заполняли заявку, это окошко заняли 😔\n"
            "Выберите, пожалуйста, другое время.",
            reply_markup=remove_keyboard,
        )
        await _ask_slot(message, state, db)
        return
    delivered = await _notify_admins(bot, config, application)
    if delivered == 0:
        logger.error("Заявка #%s сохранена, но админам не доставлена", application.id)
    await reminders.schedule(application)
    await state.clear()
    await message.answer(
        "Спасибо! Заявка принята ✅\n\n"
        f"🕒 Время: <b>{texts.slot_text(application.starts_at)}</b>\n"
        "Мы свяжемся с вами по указанному номеру.\n"
        "Чтобы оставить ещё одну заявку, нажмите /start.",
        reply_markup=remove_keyboard,
    )
    logger.info("Заявка #%s от пользователя %s", application.id, message.from_user.id)


@router.message(ApplicationForm.confirm, F.text == BTN_RESTART)
async def restart_application(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Хорошо, начнём заново 🔄")
    await _ask_address(message, state)


@router.message(ApplicationForm.confirm)
async def confirm_unknown_answer(message: Message) -> None:
    await message.answer(
        "Пожалуйста, выберите вариант кнопкой ниже 👇",
        reply_markup=confirm_keyboard(),
    )


@router.message(StateFilter(None))
async def unknown_message(message: Message) -> None:
    await message.answer(
        "Я принимаю заявки на услуги 🙂\n"
        "Нажмите /start, чтобы оформить заявку, или /help – чтобы узнать больше."
    )
