import logging
from telebot import types

logger = logging.getLogger(__name__)

def register_user_handlers(bot, chess_bot):
    """Регистрация пользовательских обработчиков"""

    @bot.message_handler(commands=['register'])
    def register_command(message):
        """Команда регистрации"""
        try:
            user_id = message.from_user.id
            existing_user = chess_bot.file_storage.get_user_from_file(user_id)

            if existing_user:
                bot.reply_to(
                    message,
                    f"✅ Вы уже зарегистрированы с ником: **{existing_user}**",
                    parse_mode='Markdown'
                )
                return

            bot.reply_to(
                message,
                "📝 Введите ваш никнейм на Lichess:",
                parse_mode='Markdown'
            )
            bot.register_next_step_handler(message, process_registration)
            chess_bot.file_storage.log_activity(user_id, 'register_attempt')

        except Exception as e:
            logger.error(f"Ошибка в register_command: {e}")
            bot.reply_to(message, "❌ Произошла ошибка. Попробуйте позже.")

    def process_registration(message):
        """Обработка регистрации пользователя"""
        try:
            user_id = message.from_user.id
            lichess_username = message.text.strip()

            # Валидация никнейма
            if len(lichess_username) <= 2:
                bot.reply_to(
                    message,
                    "❌ Никнейм должен быть от 2 символов. Попробуйте еще раз.",
                    parse_mode='Markdown'
                )
                bot.register_next_step_handler(message, process_registration)
                return

            # Проверка на Lichess
            
            loading_message = bot.reply_to(
                message,
                "⏳ Проверяю профиль на Lichess...",
                parse_mode='Markdown'
            )

            profile = chess_bot.lichess_api.get_lichess_profile(lichess_username)

            if not profile:
                bot.reply_to(
                    message,
                    "❌ Пользователь с таким никнеймом не найден на Lichess. Попробуйте еще раз.",
                    parse_mode='Markdown'
                )
                bot.register_next_step_handler(message, process_registration)
                return

            # Регистрация в системе
            if chess_bot.file_storage.register_user(user_id, lichess_username):
                success_message = chess_bot.formatter.format_registration_success(lichess_username)

                try:
                    bot.delete_message(chat_id=message.chat.id, message_id=loading_message.message_id)
                    bot.reply_to(message, success_message, parse_mode='Markdown')
                except:
                    bot.edit_message_text(
                        text=success_message,
                        chat_id=message.chat.id,
                        message_id=loading_message.message_id,
                        parse_mode='Markdown'
                    )
            else:
                bot.reply_to(
                    message,
                    "❌ Этот никнейм уже зарегистрирован другим пользователем.",
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Ошибка в process_registration: {e}")
            bot.reply_to(message, "❌ Произошла ошибка регистрации.")

    @bot.message_handler(commands=['profile'])
    def profile_command(message):
        """Команда просмотра профиля с разбивкой на страницы"""
        user_id = message.from_user.id
        username = chess_bot.file_storage.get_user_from_file(user_id)

        if not username:
            bot.reply_to(
                message,
                "❌ Вы не зарегистрированы. Используйте /register для регистрации.",
                parse_mode='Markdown')
            return

        loading_message = bot.reply_to(message, "⏳ Загружаю данные профиля...", parse_mode='Markdown')

        # Получаем первую страницу профиля
        profile_text, keyboard = chess_bot.show_profile_page(user_id, username, 1)

        try:
            bot.delete_message(chat_id=message.chat.id, message_id=loading_message.message_id)
            bot.reply_to(message, profile_text, 
                        parse_mode='Markdown', 
                        disable_web_page_preview=True,
                        reply_markup=keyboard)
        except Exception as e:
            bot.edit_message_text(
                text=profile_text,
                chat_id=message.chat.id,
                message_id=loading_message.message_id,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=keyboard
            )

        chess_bot.file_storage.log_activity(user_id, 'profile_view_page_1')

    @bot.message_handler(commands=['logout'])
    def logout_command(message):
        """Команда выхода из аккаунта"""
        try:
            user_id = message.from_user.id
            username = chess_bot.file_storage.get_user_from_file(user_id)

            if not username:
                bot.reply_to(
                    message,
                    "❌ Вы не зарегистрированы в системе.",
                    parse_mode='Markdown'
                )
                return

            warning_text = chess_bot.formatter.format_logout_warning(username)
            keyboard = chess_bot.keyboards.get_logout_confirmation_keyboard(username)

            bot.reply_to(
                message,
                warning_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            chess_bot.file_storage.log_activity(user_id, 'logout_attempt')

        except Exception as e:
            logger.error(f"Ошибка в logout_command: {e}")
            bot.reply_to(message, "❌ Произошла ошибка.")

    @bot.message_handler(commands=['leaders'])
    def leaders_command(message):
        """Команда просмотра многостраничного лидерборда команды"""
        user_id = message.from_user.id
        username = chess_bot.file_storage.get_user_from_file(user_id)

        if not username:
            bot.reply_to(
                message,
                "❌ Вы не зарегистрированы. Используйте /register для регистрации.",
                parse_mode='Markdown')
            return

        loading_message = bot.reply_to(message, "⏳ Загружаю лидерборд команды...", parse_mode='Markdown')

        try:
            # Получаем первую страницу лидерборда
            leaders_message, keyboard = chess_bot.formatter.format_leaders_page(
                username, 
                chess_bot.tournament_service,
                page=1
            )

            # Удаляем сообщение о загрузке и отправляем лидерборд
            bot.delete_message(chat_id=message.chat.id, message_id=loading_message.message_id)
            bot.reply_to(message, leaders_message, 
                        parse_mode='Markdown', 
                        disable_web_page_preview=True,
                        reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Ошибка в leaders_command: {e}")
            try:
                bot.edit_message_text(
                    text="❌ Ошибка при загрузке лидерборда команды",
                    chat_id=message.chat.id,
                    message_id=loading_message.message_id,
                    parse_mode='Markdown'
                )
            except:
                bot.reply_to(message, "❌ Ошибка при загрузке лидерборда команды", parse_mode='Markdown')

        chess_bot.file_storage.log_activity(user_id, 'leaders_view_page_1')

    # Обработчики кнопок

    @bot.message_handler(func=lambda msg: msg.text == "📝 Регистрация")
    def registration_button(message):
        register_command(message)

    @bot.message_handler(func=lambda message: message.text == "👤 Мой профиль")
    def profile_button(message):
        profile_command(message)

    @bot.message_handler(func=lambda msg: msg.text == "🚪 Выйти из аккаунта")
    def logout_button(message):
        logout_command(message)

    @bot.message_handler(func=lambda message: message.text == "🏆 Лидерборд команды")
    def leaders_button(message):
        leaders_command(message)

    logger.info("Пользовательские обработчики зарегистрированы")
