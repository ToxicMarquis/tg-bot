from __future__ import annotations
import logging
from datetime import timedelta
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import texts
import timeutils
from config import Config
from db import Application, Database

logger = logging.getLogger(__name__)
REMIND_BEFORE = timedelta(hours=24)
SWEEP_MINUTES = 15


class ReminderService:
    def __init__(self, bot: Bot, db: Database, config: Config) -> None:
        self._bot = bot
        self._db = db
        self._config = config
        try:
            self._scheduler = AsyncIOScheduler(timezone=config.timezone)
        except Exception:
            logger.warning("Планировщик не принял пояс %r, работаю в UTC", config.timezone)
            self._scheduler = AsyncIOScheduler(timezone="UTC")

    async def start(self) -> None:
        self._scheduler.add_job(
            self.sweep,
            trigger="interval",
            minutes=SWEEP_MINUTES,
            id="reminders:sweep",
            replace_existing=True,
        )
        self._scheduler.start()
        await self.sweep()
        logger.info("Планировщик напоминаний запущен")

    async def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    async def sweep(self) -> None:
        for application in await self._db.pending_reminders():
            await self.schedule(application)

    async def schedule(self, application: Application) -> None:
        if application.starts_at is None or application.reminded:
            return
        run_at = application.starts_at - REMIND_BEFORE
        if run_at <= timeutils.now():
            if application.created_at >= run_at:
                await self._db.mark_reminded(application.id)
                return
            await self.send(application.id)
            return
        self._scheduler.add_job(
            self.send,
            trigger="date",
            run_date=timeutils.localize(run_at),
            args=(application.id,),
            id=f"reminder:{application.id}",
            replace_existing=True,
            misfire_grace_time=3600,
            coalesce=True,
        )

    async def send(self, application_id: int) -> None:
        application = await self._db.get_application(application_id)
        if application is None or application.reminded or application.starts_at is None:
            return
        if application.starts_at <= timeutils.now():
            await self._db.mark_reminded(application_id)
            return
        delivered = 0
        for admin_id in self._config.admin_ids:
            try:
                await self._bot.send_message(admin_id, texts.reminder(application))
            except TelegramAPIError as error:
                logger.error("Напоминание не ушло админу %s: %s", admin_id, error)
            else:
                delivered += 1
        if delivered:
            await self._db.mark_reminded(application_id)
            logger.info("Напоминание по заявке #%s отправлено", application_id)
