import logging
from telebot import types

logger = logging.getLogger(__name__)

def register_base_handlers(bot, chess_bot):
    """Регистрация базовых обработчиков команд"""

    @bot.message_handler(commands=['start'])
    def start_command(message):
        """Приветственное сообщение"""
        try:
            user_id = message.from_user.id
            username = chess_bot.file_storage.get_user_from_file(user_id)

            if username:
                welcome_text = chess_bot.formatter.format_welcome_registered(username)
                keyboard = chess_bot.keyboards.get_main_keyboard()
            else:
                welcome_text = chess_bot.formatter.format_welcome_new()
                keyboard = chess_bot.keyboards.get_main_keyboard()

            bot.reply_to(message, welcome_text, reply_markup=keyboard, parse_mode='Markdown')
            chess_bot.file_storage.log_activity(user_id, 'start_command')

        except Exception as e:
            logger.error(f"Ошибка в start_command: {e}")
            bot.reply_to(message, "❌ Произошла ошибка. Попробуйте позже.")

    @bot.message_handler(commands=['help'])
    def help_command(message):
        """Команда помощи"""
        try:
            user_id = message.from_user.id
            help_text = chess_bot.formatter.format_help_message(
                chess_bot.is_developer(user_id)
            )

            bot.reply_to(message, help_text, parse_mode='Markdown')
            chess_bot.file_storage.log_activity(user_id, 'help_command')

        except Exception as e:
            logger.error(f"Ошибка в help_command: {e}")
            bot.reply_to(message, "❌ Произошла ошибка. Попробуйте позже.")

    @bot.message_handler(commands=['stats'])
    def stats_command(message):
        """Команда статистики бота"""
        try:
            stats_data = chess_bot.file_storage.get_basic_stats()
            stats_text = chess_bot.formatter.format_stats_message(stats_data)

            bot.reply_to(message, stats_text, parse_mode='Markdown')
            chess_bot.file_storage.log_activity(message.from_user.id, 'stats_command')

        except Exception as e:
            logger.error(f"Ошибка в stats_command: {e}")
            bot.reply_to(message, "❌ Ошибка получения статистики")

    # Обработчики кнопок основного меню
    @bot.message_handler(func=lambda msg: msg.text == "❓ Помощь")
    def help_button(message):
        help_command(message)

    @bot.message_handler(func=lambda msg: msg.text == "📊 Статистика")
    def stats_button(message):
        stats_command(message)

    logger.info("Базовые обработчики зарегистрированы")
