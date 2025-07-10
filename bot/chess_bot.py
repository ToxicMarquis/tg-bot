import logging
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import Config
from .services.file_storage import FileStorageService
from .services.lichess_api import LichessAPIService
from .services.user_service import UserService
from .services.tournament_service import TournamentService
from .utils.keyboards import KeyboardManager
from .utils.formatters import MessageFormatter
from .utils.validators import Validator

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
            self.user_service = UserService()
            self.tournament_service = TournamentService()

            # Инициализация утилит
            self.keyboards = KeyboardManager()
            self.formatter = MessageFormatter()
            self.validator = Validator()

            # Регистрация всех обработчиков
            self._register_all_handlers()

            logger.info("ChessBot успешно инициализирован")

        except Exception as e:
            logger.error(f"Ошибка инициализации ChessBot: {e}")
            raise

    def _register_all_handlers(self):
        """Регистрация всех обработчиков команд"""
        try:
            # Команда /start
            @self.bot.message_handler(commands=['start'])
            def start_command(message):
                self.handle_start(message)

            # Команда /help
            @self.bot.message_handler(commands=['help'])
            def help_command(message):
                self.handle_help(message)

            # Команда /app
            @self.bot.message_handler(commands=['app'])
            def app_command(message):
                self.handle_app(message)

            # Команда /register (для разработчика)
            @self.bot.message_handler(commands=['register'])
            def register_command(message):
                if message.from_user.id == Config.DEVELOPER_ID:
                    self.handle_register(message)

            logger.info("Все обработчики команд зарегистрированы")

        except Exception as e:
            logger.error(f"Ошибка регистрации обработчиков: {e}")
            raise

    def handle_start(self, message):
        """Обработчик команды /start"""
        try:
            welcome_text = """🏆 Добро пожаловать в Chess Tournament Bot! 

Этот бот создан для участников шахматных турниров и любителей шахмат.

🎯 Основные возможности:
• 📊 Просмотр профиля и статистики
• 🏅 Система уровней и опыта
• ♟️ Игра против ИИ (5 уровней сложности)
• 🏆 Таблица лидеров
• 🛍️ Магазин для кастомизации профиля

📱 Для полного функционала используйте команду /app

❓ Нужна помощь? Используйте /help"""

            self.bot.send_message(message.chat.id, welcome_text)

        except Exception as e:
            logger.error(f"Ошибка в handle_start: {e}")
            self.bot.send_message(message.chat.id, "Произошла ошибка при обработке команды.")

    def handle_help(self, message):
        """Обработчик команды /help"""
        try:
            help_text = """📚 Справка по Chess Tournament Bot

🎮 Основные команды:
• /start - Приветственное сообщение
• /help - Эта справка
• /app - Открыть приложение

🔐 Регистрация для новых пользователей:
Если вы не зарегистрированы в системе, для доступа к приложению необходимо:

1. Добавить в описание вашего Telegram-аккаунта слово "univerify"
2. Нажать кнопку "Войти в приложение"
3. Система автоматически проверит ваш аккаунт
4. После успешной проверки вы получите доступ к приложению

⚠️ Важно: 
• Используйте только латинские буквы и цифры в никнейме
• Никнейм должен содержать от 3 до 20 символов
• Запрещены специальные символы и SQL-элементы

🎯 Возможности приложения:
• Просмотр профиля с рейтингами Lichess
• Система уровней (опыт рассчитывается по формуле: Очки × 10 + Посещаемость × 25 + Средний перформанс ÷ 100)
• Шахматный симулятор с 5 уровнями сложности
• Магазин для кастомизации профиля
• Таблица лидеров

💰 Система монет:
• Получайте монеты за победы над ИИ
• Покупайте кастомизацию профиля
• Открывайте новые возможности с повышением уровня

🎨 Кастомизация:
• 1 уровень: собственные обои (50 монет)
• 3 уровень: собственный аватар (100 монет)  
• 5 уровень: собственный баннер (200 монет)
• 6+ уровень: эффекты для аватара и профиля

Удачи в турнирах! ♟️"""

            self.bot.send_message(message.chat.id, help_text)

        except Exception as e:
            logger.error(f"Ошибка в handle_help: {e}")
            self.bot.send_message(message.chat.id, "Произошла ошибка при обработке команды.")

    def handle_app(self, message):
        """Обработчик команды /app"""
        try:
            username = message.from_user.username
            user_id = message.from_user.id

            if not username:
                self.bot.send_message(message.chat.id, 
                    "❌ Для использования приложения необходимо установить username в Telegram.")
                return

            # Проверяем, есть ли пользователь в базе
            if self.user_service.user_exists(username):
                # Пользователь существует, открываем приложение
                keyboard = InlineKeyboardMarkup()
                webapp_button = InlineKeyboardButton(
                    "🎮 Открыть приложение", 
                    web_app=WebAppInfo(url=f"{Config.WEB_APP_URL}?user={username}")
                )
                keyboard.add(webapp_button)

                self.bot.send_message(
                    message.chat.id, 
                    f"🎯 Добро пожаловать, {username}!\n\n" +
                    "Нажмите кнопку ниже, чтобы открыть приложение:",
                    reply_markup=keyboard
                )
            else:
                # Новый пользователь, нужна регистрация
                keyboard = InlineKeyboardMarkup()
                register_button = InlineKeyboardButton(
                    "📝 Зарегистрироваться", 
                    web_app=WebAppInfo(url=f"{Config.WEB_APP_URL}?register={username}")
                )
                keyboard.add(register_button)

                self.bot.send_message(
                    message.chat.id, 
                    f"👋 Добро пожаловать, {username}!\n\n" +
                    "🔐 Для регистрации выполните следующие шаги:\n" +
                    "1. Добавьте слово 'univerify' в описание вашего аккаунта\n" +
                    "2. Нажмите кнопку 'Зарегистрироваться'\n" +
                    "3. Дождитесь подтверждения\n\n" +
                    "После успешной регистрации вы получите доступ ко всем функциям!",
                    reply_markup=keyboard
                )

        except Exception as e:
            logger.error(f"Ошибка в handle_app: {e}")
            self.bot.send_message(message.chat.id, "Произошла ошибка при обработке команды.")

    def handle_register(self, message):
        """Обработчик команды /register (только для разработчика)"""
        try:
            if len(message.text.split()) < 2:
                self.bot.send_message(message.chat.id, "Использование: /register <username>")
                return

            username = message.text.split()[1]

            if self.user_service.register_user(username):
                self.bot.send_message(message.chat.id, f"✅ Пользователь {username} успешно зарегистрирован!")
            else:
                self.bot.send_message(message.chat.id, f"❌ Ошибка при регистрации пользователя {username}")

        except Exception as e:
            logger.error(f"Ошибка в handle_register: {e}")
            self.bot.send_message(message.chat.id, "Произошла ошибка при обработке команды.")

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
