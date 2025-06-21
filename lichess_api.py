import logging
import time
import berserk
from typing import Optional, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class LichessAPIService:
    """Сервис для работы с Lichess API"""

    def __init__(self):
        """Инициализация Lichess API клиента"""
        try:
            if Config.LICHESS_TOKEN:
                session = berserk.TokenSession(Config.LICHESS_TOKEN)
                self.client = berserk.Client(session=session)
                logger.info("Lichess API клиент успешно инициализирован")
            else:
                self.client = None
                logger.warning("Lichess токен не найден, API недоступен")

        except Exception as e:
            logger.error(f"Ошибка инициализации Lichess API: {e}")
            self.client = None

    def get_lichess_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Получение профиля игрока с Lichess"""
        if not self.client:
            logger.error("Lichess клиент не инициализирован")
            return None

        try:
            profile = self.client.users.get_public_data(username)

            # Соблюдаем лимит API
            time.sleep(Config.LICHESS_API_DELAY)

            logger.info(f"Профиль {username} успешно получен с Lichess")
            return profile

        except Exception as e:
            logger.error(f"Ошибка получения профиля {username}: {e}")
            return None

    def check_user_exists(self, username: str) -> bool:
        """Проверка существования пользователя на Lichess"""
        profile = self.get_lichess_profile(username)
        return profile is not None

    def get_user_rating(self, username: str, time_control: str = 'blitz') -> Optional[int]:
        """Получение рейтинга пользователя по конкретному контролю времени"""
        profile = self.get_lichess_profile(username)

        if not profile:
            return None

        try:
            perfs = profile.get('perfs', {})
            time_control_data = perfs.get(time_control, {})
            return time_control_data.get('rating')

        except Exception as e:
            logger.error(f"Ошибка получения рейтинга {time_control} для {username}: {e}")
            return None

    def get_user_games_count(self, username: str) -> Optional[int]:
        """Получение общего количества игр пользователя"""
        profile = self.get_lichess_profile(username)

        if not profile:
            return None

        try:
            count = profile.get('count', {})
            return count.get('all', 0)

        except Exception as e:
            logger.error(f"Ошибка получения количества игр для {username}: {e}")
            return None
