from __future__ import annotations
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, ErrorEvent
import timeutils
from config import Config, ConfigError, load_config
from db import Database
from handlers import get_router
from reminders import ReminderService

logger = logging.getLogger(__name__)
USER_COMMANDS = [
    BotCommand(command="start", description="Оставить заявку"),
    BotCommand(command="cancel", description="Отменить заполнение"),
    BotCommand(command="help", description="Помощь"),
]
ADMIN_COMMANDS = USER_COMMANDS + [
    BotCommand(command="admin", description="Панель администратора")
]


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


def create_bot(config: Config) -> Bot:
    session = None
    if config.api_base_url:
        session = AiohttpSession(api=TelegramAPIServer.from_base(config.api_base_url))
        logger.info("Запросы к Telegram идут через прокси: %s", config.api_base_url)
    return Bot(
        token=config.bot_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


async def set_commands(bot: Bot, config: Config) -> None:
    await bot.set_my_commands(USER_COMMANDS)
    for admin_id in config.admin_ids:
        try:
            await bot.set_my_commands(
                ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except TelegramAPIError as error:
            logger.warning("Не удалось задать команды админу %s: %s", admin_id, error)


def register_error_handler(dp: Dispatcher) -> None:
    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        logger.exception("Ошибка при обработке обновления: %s", event.exception)
        message = getattr(event.update, "message", None)
        if message is not None:
            try:
                await message.answer(
                    "Что-то пошло не так 😔\n"
                    "Попробуйте ещё раз или начните заново: /start"
                )
            except Exception:  # noqa: BLE001
                logger.exception("Не удалось отправить пользователю сообщение об ошибке")
        return True


async def main() -> None:
    setup_logging()
    try:
        config: Config = load_config()
    except ConfigError as error:
        logger.error("Некорректная конфигурация: %s", error)
        sys.exit(1)
    timeutils.configure(config.timezone)
    db = Database(config.db_path)
    await db.connect()
    bot = create_bot(config)
    reminders = ReminderService(bot=bot, db=db, config=config)
    dp = Dispatcher(storage=MemoryStorage())
    dp["config"] = config
    dp["db"] = db
    dp["reminders"] = reminders
    dp.include_router(get_router())
    register_error_handler(dp)
    try:
        await set_commands(bot, config)
        bot_info = await bot.get_me()
        logger.info(
            "Бот @%s запущен. Заявки уходят: %s", bot_info.username, config.admin_ids
        )
        await reminders.start()
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await reminders.shutdown()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
