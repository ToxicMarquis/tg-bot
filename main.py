import logging
import asyncio
import os
from bot.chess_bot import ChessBot
from config import Config
from keep_alive import keep_alive

def setup_logging():
    """Настройка системы логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """Главная функция запуска бота"""
    try:
        # Создание директорий если не существуют
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        os.makedirs('tournaments', exist_ok=True)
        os.makedirs('webapp/static', exist_ok=True)

        # Настройка логирования
        setup_logging()
        logger = logging.getLogger(__name__)

        # Активация keep_alive для UptimeRobot
        keep_alive()

        # Валидация конфигурации
        if not Config.BOT_TOKEN or not Config.LICHESS_TOKEN:
            raise ValueError("Отсутствуют необходимые токены в переменных окружения")

        # Инициализация и запуск бота
        chess_bot = ChessBot()
        logger.info("Запуск шахматного бота...")

        chess_bot.run()

    except Exception as e:
        logging.error(f"Критическая ошибка запуска: {e}")
        raise

if __name__ == '__main__':
    main()
