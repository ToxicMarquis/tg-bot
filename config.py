import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Config:
    """Центральная конфигурация приложения"""

    # Токены API
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    LICHESS_TOKEN = "lip_U4DaGygVrb4OkbXsdGhl"

    # ID разработчика
    DEVELOPER_ID = 1834341648

    # Настройки файлового хранилища
    USERS_FILE = 'data/users.txt'
    ACTIVITY_FILE = 'data/activity.txt'
    TITLES_FILE = 'data/titles.json'
    TOURNAMENTS_DIR = 'tournaments/'

    # Настройки веб-сервера для UptimeRobot
    WEB_SERVER_HOST = '0.0.0.0'
    WEB_SERVER_PORT = 8080

    # Настройки логирования
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/bot.log'

    # Лимиты API
    LICHESS_API_DELAY = 1.0  # секунд между запросами

    # Настройки сообщений
    MAX_MESSAGE_LENGTH = 4000

    @classmethod
    def validate(cls):
        """Валидация конфигурации"""
        required_vars = ['BOT_TOKEN', 'LICHESS_TOKEN']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]

        if missing_vars:
            raise ValueError(f"Отсутствуют переменные окружения: {', '.join(missing_vars)}")

        return True
