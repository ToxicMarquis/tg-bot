from flask import Flask
from threading import Thread
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return "Chess Bot is alive! 🏁♟️"

@app.route('/health')
def health():
    return {"status": "healthy", "service": "chess-telegram-bot"}

@app.route('/status')
def status():
    return {
        "status": "running",
        "bot": "Chess Telegram Bot",
        "version": "2.0.0",
        "uptime": "online"
    }

def run():
    """Запуск веб-сервера"""
    try:
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        logger.error(f"Ошибка запуска веб-сервера: {e}")

def keep_alive():
    """Поддержание работы бота для UptimeRobot"""
    try:
        server = Thread(target=run)
        server.daemon = True
        server.start()
        logger.info("Keep-alive сервер запущен на порту 8080")
    except Exception as e:
        logger.error(f"Ошибка запуска keep-alive сервера: {e}")
