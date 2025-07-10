import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Config:
    """Центральная конфигурация приложения"""

    # Токены API
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    LICHESS_TOKEN = os.environ.get('LICHESS_TOKEN')

    # ID разработчика
    DEVELOPER_ID = 1834341648

    # Настройки файлового хранилища
    USERS_FILE = 'data/users.txt'
    ACTIVITY_FILE = 'data/activity.txt'
    TITLES_FILE = 'data/titles.json'
    APP_DB_FILE = 'data/app_db.json'
    TOURNAMENTS_DIR = 'tournaments/'

    # Настройки веб-сервера
    WEB_SERVER_HOST = '0.0.0.0'
    WEB_SERVER_PORT = 8080
    WEB_APP_URL = os.environ.get('WEB_APP_URL', 'https://yourdomain.com/webapp')

    # Настройки логирования
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/bot.log'

    # Лимиты API
    LICHESS_API_DELAY = 1.0  # секунд между запросами

    # Настройки сообщений
    MAX_MESSAGE_LENGTH = 4000

    # Настройки уровней
    BASE_XP_REQUIREMENT = 50
    XP_MULTIPLIER = 1.5

    @classmethod
    def validate(cls):
        """Валидация конфигурации"""
        required_vars = ['BOT_TOKEN', 'LICHESS_TOKEN']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]

        if missing_vars:
            raise ValueError(f"Отсутствуют переменные окружения: {', '.join(missing_vars)}")

        return True

    @classmethod
    def calculate_xp_requirement(cls, level):
        """Расчет требуемого опыта для уровня"""
        return int(cls.BASE_XP_REQUIREMENT * (cls.XP_MULTIPLIER ** (level - 1)))

    @classmethod
    def calculate_level_from_xp(cls, total_xp):
        """Расчет уровня по общему опыту"""
        level = 1
        accumulated_xp = 0
        while accumulated_xp < total_xp:
            xp_needed = cls.calculate_xp_requirement(level)
            if accumulated_xp + xp_needed > total_xp:
                break
            accumulated_xp += xp_needed
            level += 1
        return level, accumulated_xp
