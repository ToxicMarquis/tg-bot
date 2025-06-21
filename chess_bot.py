import logging
import telebot
from config import Config
from .services.file_storage import FileStorageService
from .services.lichess_api import LichessAPIService
from .services.tournament_service import TournamentService
from .utils.keyboards import KeyboardManager
from .utils.formatters import MessageFormatter

# Импорт всех обработчиков
from .handlers.base_handlers import register_base_handlers
from .handlers.user_handlers import register_user_handlers
from .handlers.dev_handlers import register_dev_handlers
from .handlers.callback_handlers import register_callback_handlers

logger = logging.getLogger(__name__)

class ChessBot:
    """Главный класс шахматного Telegram-бота"""

    def __init__(self):
        """Инициализация бота и всех сервисов"""
        try:
            # Валидация конфигурации
            Config.validate()

            # Инициализация Telegram бота
            self.bot = telebot.TeleBot(Config.BOT_TOKEN)
            
            # Инициализация сервисов
            self.file_storage = FileStorageService()
            self.lichess_api = LichessAPIService()
            self.tournament_service = TournamentService()

            # Инициализация утилит
            self.keyboards = KeyboardManager()
            self.formatter = MessageFormatter()

            # Регистрация всех обработчиков
            self._register_all_handlers()

            logger.info("ChessBot успешно инициализирован")

        except Exception as e:
            logger.error(f"Ошибка инициализации ChessBot: {e}")
            raise

    def _register_all_handlers(self):
        """Регистрация всех обработчиков команд"""
        try:
            register_base_handlers(self.bot, self)
            register_user_handlers(self.bot, self)
            register_dev_handlers(self.bot, self)
            register_callback_handlers(self.bot, self)

            logger.info("Все обработчики команд зарегистрированы")

        except Exception as e:
            logger.error(f"Ошибка регистрации обработчиков: {e}")
            raise

    def show_profile_page(self, username: str, page: int = 1) -> tuple:
        """Отображение определенной страницы профиля"""
        # Загрузка данных
        titles_data = self.file_storage.load_titles_from_file()
        tournament_data = self.tournament_service.load_tournament_csv_data()
        profile = self.lichess_api.get_lichess_profile(username)

        if not profile:
            return "❌ Не удалось получить данные профиля", None

        # Выбор страницы для отображения
        if page == 1:
            message = self.formatter.format_ratings_page(username, profile, titles_data)
        elif page == 2:
            message = self.formatter.format_games_page(username, profile)
        elif page == 3:
            message = self.tournament_service.format_tournaments_page(username, tournament_data)
        else:
            message = "❌ Неверный номер страницы"
            page = 1

        keyboard = self.keyboards.get_profile_page_keyboard(page, username)
        return message, keyboard

    
    def is_developer(self, user_id: int) -> bool:
        """Проверка прав разработчика"""
        return user_id == Config.DEVELOPER_ID

    def run(self):
        """Запуск бота"""
        try:
            # Проверка подключения к Telegram API
            bot_info = self.bot.get_me()
            logger.info(f"Бот запущен: @{bot_info.username}")

            # Запуск бесконечного polling
            self.bot.infinity_polling(timeout=20)

        except Exception as e:
            logger.error(f"Критическая ошибка работы бота: {e}")
            raise

        finally:
            logger.info("Бот остановлен")
