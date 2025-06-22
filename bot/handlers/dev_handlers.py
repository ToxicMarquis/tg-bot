import logging
from config import Config
import time
from threading import Thread
from telebot import types
from telebot.apihelper import ApiTelegramException

logger = logging.getLogger(__name__)

def register_dev_handlers(bot, chess_bot):
    """Регистрация обработчиков разработчика"""

    @bot.message_handler(commands=['dev'])
    def developer_menu(message):
        """Меню разработчика"""
        if not chess_bot.is_developer(message.from_user.id):
            bot.reply_to(message, "❌ У вас нет доступа к функциям разработчика.")
            return

        try:
            dev_text = chess_bot.formatter.format_developer_menu()
            keyboard = chess_bot.keyboards.get_developer_keyboard()

            bot.reply_to(
                message,
                dev_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            chess_bot.file_storage.log_activity(message.from_user.id, 'developer_menu_access')

        except Exception as e:
            logger.error(f"Ошибка в developer_menu: {e}")
            bot.reply_to(message, "❌ Произошла ошибка.")

    @bot.message_handler(commands=['toggle_logging'])
    def toggle_logging_command(message):
        """Включение/выключение логирования сообщений"""
        if message.from_user.id != chess_bot.file_storage.DEVELOPER_ID:
            return

        # Переключаем состояние (можно добавить в конфиг)
        current_state = getattr(chess_bot, 'logging_enabled', True)
        chess_bot.logging_enabled = not current_state

        status = "включено" if chess_bot.logging_enabled else "выключено"
        bot.reply_to(message, f"🔧 Логирование сообщений {status}")

    @bot.message_handler(commands=['send_to_user'])
    def send_to_user_command(message):
        """Отправка сообщения конкретному пользователю"""
        if message.from_user.id != chess_bot.file_storage.DEVELOPER_ID:
            return

        # Парсим команду: /send_to_user USER_ID текст сообщения
        parts = message.text.split(' ', 2)

        if len(parts) < 3:
            help_text = """📤 **Отправка сообщения пользователю**

    **Формат:**
`/send_to_user USER_ID текст сообщения`

    **Пример:**
`/send_to_user 123456789 Привет! Это сообщение от администратора.`

    **Или используйте:**
`/send_to_lichess LICHESS_USERNAME текст сообщения`"""

            bot.reply_to(message, help_text, parse_mode='Markdown')
            return

        try:
            target_user_id = int(parts[1])
            message_text = parts[2]

            # Отправляем сообщение
            bot.send_message(
                target_user_id,
                f"📢 **Сообщение от администратора:**\n\n{message_text}",
                parse_mode='Markdown'
            )

            # Подтверждение разработчику
            bot.reply_to(message, f"✅ Сообщение отправлено пользователю `{target_user_id}`", parse_mode='Markdown')

            # Логируем
            chess_bot.file_storage.log_activity(target_user_id, f'admin_message_received: {message_text[:50]}...')

        except ValueError:
            bot.reply_to(message, "❌ Неверный формат USER_ID. Должно быть число.", parse_mode='Markdown')
        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка отправки: `{str(e)}`", parse_mode='Markdown')

    @bot.message_handler(commands=['send_to_lichess'])
    def send_to_lichess_command(message):
        """Отправка сообщения пользователю по Lichess никнейму"""
        if message.from_user.id != chess_bot.file_storage.DEVELOPER_ID:
            return

        parts = message.text.split(' ', 2)

        if len(parts) < 3:
            bot.reply_to(message, "❌ Формат: `/send_to_lichess LICHESS_USERNAME текст сообщения`", parse_mode='Markdown')
            return

        try:
            lichess_username = parts[1]
            message_text = parts[2]

            # Ищем пользователя в базе
            users = chess_bot.file_storage.get_all_users()
            target_user_id = None

            for user in users:
                if user['lichess_username'].lower() == lichess_username.lower():
                    target_user_id = int(user['telegram_id'])
                    break

            if not target_user_id:
                bot.reply_to(message, f"❌ Пользователь с никнеймом `{lichess_username}` не найден", parse_mode='Markdown')
                return

            # Отправляем сообщение
            bot.send_message(
                target_user_id,
                f"📢 **Сообщение от администратора:**\n\n{message_text}",
                parse_mode='Markdown'
            )

            bot.reply_to(message, f"✅ Сообщение отправлено пользователю `{lichess_username}` (ID: `{target_user_id}`)", parse_mode='Markdown')

        except Exception as e:
            bot.reply_to(message, f"❌ Ошибка отправки: `{str(e)}`", parse_mode='Markdown')

    @bot.message_handler(commands=['broadcast'])
    def broadcast_command(message):
        """Массовая рассылка всем пользователям"""
        if message.from_user.id != chess_bot.file_storage.DEVELOPER_ID:
            return

        # Получаем текст для рассылки
        parts = message.text.split(' ', 1)

        if len(parts) < 2:
            help_text = """📢 **Массовая рассылка**

    **Формат:**
    `/broadcast текст сообщения`

    **Пример:**
    `/broadcast Внимание! Завтра турнир в 20:00. Регистрация обязательна!`

    ⚠️ **Внимание:** сообщение будет отправлено ВСЕМ зарегистрированным пользователям!"""

            bot.reply_to(message, help_text, parse_mode='Markdown')
            return

        broadcast_text = parts[1]

        # Подтверждение
        confirmation_keyboard = types.InlineKeyboardMarkup()
        confirmation_keyboard.add(
            types.InlineKeyboardButton("✅ Да, отправить", callback_data=f"confirm_broadcast"),
            types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_broadcast")
        )

        # Сохраняем текст для рассылки (можно в глобальную переменную или кэш)
        chess_bot.pending_broadcast = broadcast_text

        preview_text = f"""📢 **Подтверждение массовой рассылки**

    **Сообщение для рассылки:** {broadcast_text}

    **Получателей:** {len(chess_bot.file_storage.get_all_users())} пользователей

    ⚠️ **Вы уверены, что хотите отправить это сообщение всем пользователям?**"""

        bot.reply_to(message, preview_text, parse_mode='Markdown', reply_markup=confirmation_keyboard)

    def execute_broadcast(broadcast_text: str, developer_id: int, bot_instance, chess_bot_instance):
        """
        Выполнение массовой рассылки в отдельном потоке

        Args:
            broadcast_text: Текст для рассылки
            developer_id: ID разработчика для отчетов
            bot_instance: Экземпляр Telegram бота
            chess_bot_instance: Экземпляр ChessBot
        """
        try:
            # Получаем всех пользователей
            users = chess_bot_instance.file_storage.get_all_users()

            if not users:
                bot_instance.send_message(
                    developer_id, 
                    "❌ Нет зарегистрированных пользователей для рассылки"
                )
                return

            # Статистика
            total_users = len(users)
            success_count = 0
            blocked_count = 0
            error_count = 0
            processed_count = 0

            # Экранируем текст для безопасной отправки
            safe_broadcast_text = broadcast_text.replace('_', '\\_').replace('*', '\\*')

            # Отправляем уведомление о начале
            start_message = f"""🚀 **Начинаю массовую рассылку**

    📊 **Параметры:**
    • Получателей: {total_users}
    • Длина сообщения: {len(broadcast_text)} символов

    ⏳ Процесс может занять несколько минут..."""

            bot_instance.send_message(developer_id, start_message, parse_mode='Markdown')

            # Отправляем сообщения
            for user in users:
                try:
                    user_id = int(user['telegram_id'])
                    processed_count += 1

                    # Формируем сообщение для пользователя
                    user_message = f"""📢 **Сообщение от администрации**

    {safe_broadcast_text}

    ---
    _Это сообщение отправлено всем участникам бота_"""

                    # Отправляем сообщение
                    bot_instance.send_message(
                        user_id,
                        user_message,
                        parse_mode='Markdown'
                    )

                    success_count += 1

                    # Логируем успешную отправку
                    chess_bot_instance.file_storage.log_activity(
                        user_id, 
                        f'broadcast_received: {broadcast_text[:50]}...'
                    )

                    # Пауза между отправками (соблюдение лимитов Telegram)
                    time.sleep(0.05)  # 50мс между сообщениями

                    # Отправляем прогресс каждые 25 пользователей
                    if processed_count % 25 == 0:
                        progress_message = f"""📊 **Прогресс рассылки**

    ✅ Отправлено: {success_count}
    🚫 Заблокировано: {blocked_count}
    ❌ Ошибок: {error_count}
    📈 Обработано: {processed_count}/{total_users}

    ⏳ Продолжаю рассылку..."""

                        bot_instance.send_message(
                            developer_id, 
                            progress_message, 
                            parse_mode='Markdown'
                        )

                except ApiTelegramException as telegram_error:
                    error_code = telegram_error.error_code
                    error_description = telegram_error.description.lower()

                    if error_code == 403:
                        # Пользователь заблокировал бота
                        if 'blocked' in error_description or 'bot was blocked' in error_description:
                            blocked_count += 1
                            chess_bot_instance.file_storage.log_activity(
                                int(user['telegram_id']), 
                                'broadcast_user_blocked_bot'
                            )
                        else:
                            error_count += 1
                            logger.warning(f"403 ошибка для пользователя {user['telegram_id']}: {error_description}")

                    elif error_code == 400:
                        # Пользователь не найден или деактивирован
                        if 'user not found' in error_description or 'chat not found' in error_description:
                            blocked_count += 1
                            chess_bot_instance.file_storage.log_activity(
                                int(user['telegram_id']), 
                                'broadcast_user_not_found'
                            )
                        else:
                            error_count += 1
                            logger.warning(f"400 ошибка для пользователя {user['telegram_id']}: {error_description}")

                    else:
                        # Другие ошибки Telegram
                        error_count += 1
                        logger.error(f"Telegram API ошибка {error_code} для пользователя {user['telegram_id']}: {error_description}")

                except ValueError as ve:
                    # Неверный формат user_id
                    error_count += 1
                    logger.error(f"Неверный telegram_id: {user.get('telegram_id', 'Unknown')} - {ve}")

                except Exception as e:
                    # Любые другие ошибки
                    error_count += 1
                    logger.error(f"Неожиданная ошибка при отправке пользователю {user.get('telegram_id', 'Unknown')}: {e}")

                    # При критических ошибках делаем паузу
                    time.sleep(1)

            # Вычисляем финальную статистику
            success_rate = round((success_count / total_users) * 100, 1) if total_users > 0 else 0

            # Отправляем финальный отчет
            final_report = f"""✅ **Массовая рассылка завершена**

    📊 **Детальная статистика:**
    • 👥 Всего пользователей: {total_users}
    • ✅ Успешно доставлено: {success_count}
    • 🚫 Заблокировали бота: {blocked_count}
    • ❌ Ошибки доставки: {error_count}

    📈 **Показатели:**
    • Успешность доставки: {success_rate}%
    • Активных пользователей: {success_count}/{total_users}

    💬 **Текст рассылки:** {broadcast_text[:200]}{'...' if len(broadcast_text) > 200 else ''}
    🕐 **Время выполнения:** ~{round(processed_count * 0.05 / 60, 1)} мин"""

            bot_instance.send_message(developer_id, final_report, parse_mode='Markdown')

            # Логируем завершение рассылки
            chess_bot_instance.file_storage.log_activity(
                developer_id, 
                f'broadcast_completed: {success_count}/{total_users} success_rate={success_rate}%'
            )

            logger.info(f"Массовая рассылка завершена: {success_count}/{total_users} успешно")

        except Exception as critical_error:
            # Критическая ошибка всей рассылки
            error_message = f"""❌ **Критическая ошибка рассылки**

    🚨 **Ошибка:** `{str(critical_error)}`

    📊 **На момент ошибки:**
    • Обработано: {processed_count if 'processed_count' in locals() else 0}
    • Успешно: {success_count if 'success_count' in locals() else 0}

    🔧 Обратитесь к разработчику для диагностики."""

            bot_instance.send_message(developer_id, error_message, parse_mode='Markdown')

            logger.critical(f"Критическая ошибка массовой рассылки: {critical_error}")

            # Логируем критическую ошибку
            try:
                chess_bot_instance.file_storage.log_activity(
                    developer_id, 
                    f'broadcast_critical_error: {str(critical_error)[:100]}'
                )
            except:
                pass  # Если даже логирование не работает

    def start_broadcast_thread(broadcast_text: str, developer_id: int, bot_instance, chess_bot_instance):
        """
        Запуск рассылки в отдельном потоке

        Args:
            broadcast_text: Текст для рассылки
            developer_id: ID разработчика
            bot_instance: Экземпляр бота
            chess_bot_instance: Экземпляр ChessBot
        """
        try:
            broadcast_thread = Thread(
                target=execute_broadcast,
                args=(broadcast_text, developer_id, bot_instance, chess_bot_instance),
                name="BroadcastThread"
            )
            broadcast_thread.daemon = True  # Поток завершится при завершении основной программы
            broadcast_thread.start()

            logger.info(f"Поток массовой рассылки запущен для {len(chess_bot_instance.file_storage.get_all_users())} пользователей")

        except Exception as e:
            logger.error(f"Ошибка запуска потока рассылки: {e}")
            bot_instance.send_message(
                developer_id, 
                f"❌ Ошибка запуска рассылки: `{str(e)}`", 
                parse_mode='Markdown'
            )

    @bot.callback_query_handler(func=lambda call: call.data == 'confirm_broadcast')
    def confirm_broadcast(call):
        """Подтверждение массовой рассылки"""
        if call.from_user.id != chess_bot.file_storage.DEVELOPER_ID:
            return

        # Получаем сохраненный текст
        broadcast_text = getattr(chess_bot, 'pending_broadcast', None)

        if not broadcast_text:
            bot.answer_callback_query(call.id, "❌ Текст рассылки не найден")
            return

        # Редактируем сообщение
        bot.edit_message_text(
            "🚀 **Рассылка запущена**\n\nВы получите детальные отчеты о прогрессе.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='Markdown'
        )

        # Запускаем рассылку через вспомогательную функцию
        start_broadcast_thread(broadcast_text, call.from_user.id, bot, chess_bot)

        # Очищаем сохраненный текст
        chess_bot.pending_broadcast = None

        bot.answer_callback_query(call.id, "✅ Рассылка запущена в фоновом режиме")

    @bot.callback_query_handler(func=lambda call: call.data == 'cancel_broadcast')
    def cancel_broadcast(call):
        """Отмена массовой рассылки"""
        if call.from_user.id != chess_bot.file_storage.DEVELOPER_ID:
            return

        bot.edit_message_text(
            "❌ **Рассылка отменена**",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='MarkdownV2'
        )

        # Очищаем сохраненный текст
        chess_bot.pending_broadcast = None

        bot.answer_callback_query(call.id, "❌ Рассылка отменена")

    # Обработчики кнопок разработчика
    
    @bot.message_handler(func=lambda msg: msg.text == "👥 Все пользователи")
    def dev_all_users(message):
        """Список всех пользователей"""
        if not chess_bot.is_developer(message.from_user.id):
            return

        try:
            users = chess_bot.file_storage.get_all_users()
            users_text = chess_bot.formatter.format_all_users(users)

            # Разбиваем длинные сообщения
            if len(users_text) > Config.MAX_MESSAGE_LENGTH:
                chunks = [users_text[i:i+Config.MAX_MESSAGE_LENGTH] 
                         for i in range(0, len(users_text), Config.MAX_MESSAGE_LENGTH)]
                for chunk in chunks:
                    bot.send_message(message.chat.id, chunk, parse_mode='Markdown')
            else:
                bot.reply_to(message, users_text, parse_mode='Markdown', disable_web_page_preview=True)

            chess_bot.file_storage.log_activity(message.from_user.id, 'dev_all_users')

        except Exception as e:
            logger.error(f"Ошибка в dev_all_users: {e}")
            bot.reply_to(message, "❌ Произошла ошибка.")

    @bot.message_handler(func=lambda msg: msg.text == "📈 Детальная статистика")
    def dev_detailed_stats(message):
        """Детальная статистика"""
        if not chess_bot.is_developer(message.from_user.id):
            return

        try:
            users = chess_bot.file_storage.get_all_users()
            activity_stats = chess_bot.file_storage.get_activity_stats()

            stats_text = chess_bot.formatter.format_detailed_stats(users, activity_stats)
            bot.reply_to(message, stats_text, parse_mode='Markdown')
            chess_bot.file_storage.log_activity(message.from_user.id, 'dev_detailed_stats')

        except Exception as e:
            logger.error(f"Ошибка в dev_detailed_stats: {e}")
            bot.reply_to(message, "❌ Произошла ошибка.")

    @bot.message_handler(func=lambda message: message.text == "📤 Отправить сообщение")
    def send_message_button(message):
        if message.from_user.id != chess_bot.file_storage.DEVELOPER_ID:
            return

        help_text = """📤 **Отправка сообщений**

    **Доступные команды:**

    `/send_to_user USER_ID текст` - отправить по Telegram ID
    `/send_to_lichess USERNAME текст` - отправить по Lichess никнейму

    **Примеры:**
    `/send_to_user 123456789 Привет!`
    `/send_to_lichess ModerMark Как дела?`"""

        bot.reply_to(message, help_text, parse_mode='Markdown')

    @bot.message_handler(func=lambda message: message.text == "📢 Массовая рассылка")
    def broadcast_button(message):
        if message.from_user.id != chess_bot.file_storage.DEVELOPER_ID:
            return

        help_text = """📢 **Массовая рассылка**

    **Команда:**
    `/broadcast текст сообщения`

    ⚠️ **Внимание:** сообщение будет отправлено ВСЕМ зарегистрированным пользователям!

    📊 **Текущее количество пользователей:** """ + str(len(chess_bot.file_storage.get_all_users()))

        bot.reply_to(message, help_text, parse_mode='Markdown')

    @bot.message_handler(func=lambda msg: msg.text == "🗑️ Очистить логи")
    def dev_clear_logs(message):
        """Очистка логов"""
        if not chess_bot.is_developer(message.from_user.id):
            return

        try:
            if chess_bot.file_storage.clear_activity_logs():
                bot.reply_to(message, "✅ Логи активности успешно очищены")
            else:
                bot.reply_to(message, "❌ Ошибка при очистке логов")

            chess_bot.file_storage.log_activity(message.from_user.id, 'dev_clear_logs')

        except Exception as e:
            logger.error(f"Ошибка в dev_clear_logs: {e}")
            bot.reply_to(message, "❌ Произошла ошибка.")

    @bot.message_handler(func=lambda msg: msg.text == "💾 Экспорт данных")
    def dev_export_data(message):
        """Экспорт данных"""
        if not chess_bot.is_developer(message.from_user.id):
            return

        try:
            # Отправляем файлы пользователей и активности
            with open(Config.USERS_FILE, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="📁 Файл пользователей")

            with open(Config.ACTIVITY_FILE, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="📁 Файл логов активности")

            bot.reply_to(message, "✅ Данные экспортированы")
            chess_bot.file_storage.log_activity(message.from_user.id, 'dev_export_data')

        except Exception as e:
            logger.error(f"Ошибка в dev_export_data: {e}")
            bot.reply_to(message, f"❌ Ошибка экспорта: {e}")

    @bot.message_handler(func=lambda msg: msg.text == "🔄 Перезагрузить данные")
    def dev_reload_data(message):
        """Перезагрузка данных"""
        if not chess_bot.is_developer(message.from_user.id):
            return

        try:
            chess_bot.file_storage.init_text_storage()
            bot.reply_to(message, "✅ Система данных перезагружена")
            chess_bot.file_storage.log_activity(message.from_user.id, 'dev_reload_data')

        except Exception as e:
            logger.error(f"Ошибка в dev_reload_data: {e}")
            bot.reply_to(message, f"❌ Ошибка перезагрузки: {e}")

    @bot.message_handler(func=lambda msg: msg.text == "🔙 В обычное меню")
    def dev_back_to_main(message):
        """Возврат в обычное меню"""
        if not chess_bot.is_developer(message.from_user.id):
            return

        try:
            keyboard = chess_bot.keyboards.get_main_keyboard()
            bot.reply_to(
                message,
                "🔙 Возврат в обычное меню",
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Ошибка в dev_back_to_main: {e}")
            bot.reply_to(message, "❌ Произошла ошибка.")

    # Обработчик всех текстовых сообщений для логирования
    @bot.message_handler(func=lambda message: True, content_types=['text'])
    def log_all_messages(message):
        """Логирование всех сообщений разработчику"""
        try:
            # Пропускаем команды (начинающиеся с /)
            if message.text.startswith('/'):
                return

            # Пропускаем сообщения от самого разработчика
            if message.from_user.id == chess_bot.file_storage.DEVELOPER_ID:
                return

            # Получаем информацию о пользователе
            user_id = message.from_user.id
            username = message.from_user.username or "Нет username"
            first_name = message.from_user.first_name or "Нет имени"
            last_name = message.from_user.last_name or ""

            # Получаем никнейм Lichess если зарегистрирован
            lichess_username = chess_bot.file_storage.get_user_from_file(user_id)
            lichess_info = f"\n    🔗 **Lichess:** {lichess_username}" if lichess_username else "\n❌ **Не зарегистрирован**"

            # Форматируем сообщение для логирования
            log_message = f"""📨 **Новое сообщение**

    👤 **Пользователь:**
    • ID: `{user_id}`
    • Username: @{username}
    • Имя: {first_name} {last_name}
    {lichess_info}

    💬 **Сообщение:** {message.text}
    📍 **Чат:** {message.chat.type}
    🕐 **Время:** {message.date}"""

            # Отправляем разработчику
            bot.send_message(
                chess_bot.file_storage.DEVELOPER_ID,
                log_message,
                parse_mode='Markdown'
            )

            # Логируем в файл
            chess_bot.file_storage.log_activity(user_id, f'message_sent: {message.text[:50]}...')

        except Exception as e:
            logger.error(f"Ошибка логирования сообщения: {e}")

    logger.info("Обработчики разработчика зарегистрированы")
