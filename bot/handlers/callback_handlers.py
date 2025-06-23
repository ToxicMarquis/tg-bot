import logging
from threading import Thread

logger = logging.getLogger(__name__)

def register_callback_handlers(bot, chess_bot):
    """Регистрация обработчиков inline-кнопок"""

    @bot.callback_query_handler(func=lambda call: call.data.startswith('logout_confirm_'))
    def confirm_logout(call):
        """Подтверждение выхода из аккаунта"""
        try:
            user_id = call.from_user.id
            username = call.data.replace('logout_confirm_', '')

            # Удаляем пользователя из системы
            if chess_bot.file_storage.delete_user_from_storage(user_id):
                success_text = chess_bot.formatter.format_logout_success(username)

                # Редактируем сообщение и убираем кнопки
                bot.edit_message_text(
                    text=success_text,
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode='Markdown'
                )

                # Отправляем новое сообщение с основным меню
                keyboard = chess_bot.keyboards.get_main_keyboard()
                bot.send_message(
                    call.message.chat.id,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                chess_bot.file_storage.log_activity(user_id, 'account_deleted')

            else:
                error_text = "❌ Произошла ошибка при удалении аккаунта. Попробуйте позже."
                bot.edit_message_text(
                    text=error_text,
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f"Ошибка в confirm_logout: {e}")
            bot.answer_callback_query(call.id, "❌ Произошла ошибка")

    @bot.callback_query_handler(func=lambda call: call.data == 'logout_cancel')
    def cancel_logout(call):
        """Отмена выхода из аккаунта"""
        try:
            cancel_text = chess_bot.formatter.format_logout_cancel()

            bot.edit_message_text(
                text=cancel_text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='Markdown'
            )

            chess_bot.file_storage.log_activity(call.from_user.id, 'logout_cancelled')

        except Exception as e:
            logger.error(f"Ошибка в cancel_logout: {e}")
            bot.answer_callback_query(call.id, "❌ Произошла ошибка")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('profile_page_'))
    def handle_profile_navigation(call):
        """Обработка навигации по страницам профиля"""
        try:
            # Парсим данные из callback
            data_parts = call.data.split('_')

            if len(data_parts) >= 4:
                page = int(data_parts[2])
                username = '_'.join(data_parts[3:])  # На случай если в никнейме есть подчеркивания
            else:
                page = 1
                username = chess_bot.file_storage.get_user_from_file(call.from_user.id)

            # Проверяем права доступа
            user_id = call.from_user.id
            current_username = chess_bot.file_storage.get_user_from_file(user_id)

            if current_username != username and not chess_bot.is_developer(user_id):
                bot.answer_callback_query(call.id, "❌ Нет доступа к этому профилю")
                return

            # Получаем данные страницы
            profile_text, keyboard = chess_bot.show_profile_page(user_id, username, page)

            # Обновляем сообщение
            bot.edit_message_text(
                text=profile_text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=keyboard
            )

            # Логируем переход
            chess_bot.file_storage.log_activity(user_id, f'profile_view_page_{page}')

            # Уведомляем пользователя
            page_names = ["рейтингов", "игр", "турниров"]
            bot.answer_callback_query(call.id, f"📄 Страница {page_names[page-1]}")

        except Exception as e:
            logger.error(f"Ошибка навигации по профилю: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка загрузки страницы")

    @bot.callback_query_handler(func=lambda call: call.data == 'close_profile')
    def handle_close_profile(call):
        """Обработка закрытия профиля"""
        try:
            # Удаляем сообщение с профилем
            bot.delete_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )

            # Отправляем подтверждение
            bot.send_message(
                call.message.chat.id,
                "✅ Профиль закрыт",
                reply_markup=chess_bot.keyboards.get_main_keyboard()
            )

            chess_bot.file_storage.log_activity(call.from_user.id, 'profile_closed')

        except Exception as e:
            logger.error(f"Ошибка закрытия профиля: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка закрытия")

    @bot.callback_query_handler(func=lambda call: call.data in ['page_info', 'current_page'])
    def handle_page_info(call):
        """Обработка информационных кнопок"""
        if call.data == 'page_info':
            bot.answer_callback_query(call.id, "ℹ️ Текущая страница профиля")
        elif call.data == 'current_page':
            bot.answer_callback_query(call.id, "• Вы находитесь на этой странице •")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('leaders_page_'))
    def handle_leaders_navigation(call):
        """Обработка навигации по страницам лидерборда"""
        try:
            # Парсим данные из callback
            data_parts = call.data.split('_')

            if len(data_parts) >= 4:
                page = int(data_parts[2])
                username = '_'.join(data_parts[3:])  # На случай если в никнейме есть подчеркивания
            else:
                page = 1
                username = chess_bot.file_storage.get_user_from_file(call.from_user.id)

            # Проверяем права доступа
            user_id = call.from_user.id
            current_username = chess_bot.file_storage.get_user_from_file(user_id)

            if not current_username:
                bot.answer_callback_query(call.id, "❌ Вы не зарегистрированы")
                return

            # Получаем данные страницы
            leaders_message, keyboard = chess_bot.formatter.format_leaders_page(
                current_username, 
                chess_bot.tournament_service, 
                page
            )

            # Обновляем сообщение
            bot.edit_message_text(
                text=leaders_message,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=keyboard
            )

            # Логируем переход
            chess_bot.file_storage.log_activity(user_id, f'leaders_view_page_{page}')

            # Уведомляем пользователя
            bot.answer_callback_query(call.id, f"📄 Страница {page}")

        except Exception as e:
            logger.error(f"Ошибка навигации по лидерборду: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка загрузки страницы")

    @bot.callback_query_handler(func=lambda call: call.data == 'close_leaders')
    def handle_close_leaders(call):
        """Обработка закрытия лидерборда"""
        try:
            # Удаляем сообщение с лидербордом
            bot.delete_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )

            # Отправляем подтверждение
            bot.send_message(
                call.message.chat.id,
                "✅ Лидерборд закрыт",
                reply_markup=chess_bot.keyboards.get_main_keyboard()
            )

            chess_bot.file_storage.log_activity(call.from_user.id, 'leaders_closed')

        except Exception as e:
            logger.error(f"Ошибка закрытия лидерборда: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка закрытия")

    @bot.callback_query_handler(func=lambda call: call.data == 'leaders_page_info')
    def handle_leaders_page_info(call):
        bot.answer_callback_query(call.id, "ℹ️ Информация о текущей странице лидерборда")
    
    logger.info("Callback обработчики зарегистрированы")
