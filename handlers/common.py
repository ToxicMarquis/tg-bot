import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from config import Config
from keyboards import BTN_CANCEL, remove_keyboard

logger = logging.getLogger(__name__)
router = Router(name="common")


@router.message(Command("cancel"))
@router.message(F.text == BTN_CANCEL)
async def cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    await state.clear()
    if current_state is None:
        await message.answer(
            "Сейчас нет активной заявки.\nНажмите /start, чтобы оформить новую 🙂",
            reply_markup=remove_keyboard,
        )
        return
    await message.answer(
        "Отменено ❌\n\nНичего страшного – можно начать заново командой /start.",
        reply_markup=remove_keyboard,
    )


@router.message(Command("help"))
async def show_help(message: Message, config: Config) -> None:
    text = (
        "<b>Чем я помогу</b>\n"
        "Я принимаю заявки на услуги и передаю их мастеру.\n\n"
        "<b>Команды</b>\n"
        "/start – оформить заявку\n"
        "/cancel – отменить заполнение\n"
        "/help – эта справка\n\n"
        "Заполнение занимает четыре шага: адрес, телефон, вид работ и время."
    )
    if message.from_user.id in config.admin_ids:
        text += "\n\n<b>Для администратора</b>\n/admin – окошки и заявки"
    await message.answer(text)
