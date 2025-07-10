from flask import Flask, render_template, request, jsonify, send_from_directory
from threading import Thread
import logging
import os

app = Flask(__name__, 
            static_folder='webapp/static',
            template_folder='webapp')
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
        "version": "3.0.0",
        "uptime": "online"
    }

@app.route('/webapp')
def webapp():
    """Главная страница веб-приложения"""
    return render_template('index.html')

@app.route('/webapp/static/<path:filename>')
def webapp_static(filename):
    """Статические файлы для веб-приложения"""
    return send_from_directory('webapp/static', filename)

@app.route('/api/user/<username>')
def get_user_data(username):
    """API для получения данных пользователя"""
    # Здесь будет логика загрузки данных пользователя
    return jsonify({"username": username, "level": 1, "xp": 0})

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
