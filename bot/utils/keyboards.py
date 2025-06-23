from telebot import types
import logging

logger = logging.getLogger(__name__)

class KeyboardManager:
    """Менеджер клавиатур для бота"""

    def get_main_keyboard(self):
        """Основная клавиатура"""
        try:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("📝 Регистрация"))
            markup.add(types.KeyboardButton("👤 Мой профиль"))
            markup.add(types.KeyboardButton("🏆 Лидерборд команды"))
            markup.add(types.KeyboardButton("📊 Статистика"), types.KeyboardButton("❓ Помощь"))
            markup.add(types.KeyboardButton("🚪 Выйти из аккаунта"))
            return markup

        except Exception as e:
            logger.error(f"Ошибка создания основной клавиатуры: {e}")
            return None

    def get_developer_keyboard(self):
        """Расширенная клавиатура разработчика"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("👥 Все пользователи"))
        markup.add(types.KeyboardButton("📈 Детальная статистика"))
        markup.add(types.KeyboardButton("📤 Отправить сообщение"), types.KeyboardButton("📢 Массовая рассылка"))
        markup.add(types.KeyboardButton("🗑️ Очистить логи"), types.KeyboardButton("💾 Экспорт данных"))
        markup.add(types.KeyboardButton("🔄 Перезагрузить данные"))
        markup.add(types.KeyboardButton("🔙 В обычное меню"))
        return markup

    def get_logout_confirmation_keyboard(self, username: str):
        """Клавиатура подтверждения выхода"""
        try:
            markup = types.InlineKeyboardMarkup()
            confirm_btn = types.InlineKeyboardButton(
                "✅ Да, удалить аккаунт",
                callback_data=f"logout_confirm_{username}"
            )
            cancel_btn = types.InlineKeyboardButton(
                "❌ Отмена",
                callback_data="logout_cancel"
            )
            markup.add(confirm_btn)
            markup.add(cancel_btn)
            return markup

        except Exception as e:
            logger.error(f"Ошибка создания клавиатуры подтверждения: {e}")
            return None

    def get_profile_page_keyboard(self, current_page: int, user_id: int):
        """Создание клавиатуры для навигации по страницам профиля"""
        markup = types.InlineKeyboardMarkup(row_width=3)

        # Кнопки навигации
        buttons = []

        # Кнопка "Назад" (если не первая страница)
        if current_page > 1:
            buttons.append(types.InlineKeyboardButton(
                "◀️", 
                callback_data=f"profile_page_{current_page-1}_{user_id}"
            ))

        # Индикатор текущей страницы
        buttons.append(types.InlineKeyboardButton(
            f"{current_page}/3", 
            callback_data="page_info"
        ))

        # Кнопка "Вперед" (если не последняя страница)
        if current_page < 3:
            buttons.append(types.InlineKeyboardButton(
                "▶️", 
                callback_data=f"profile_page_{current_page+1}_{user_id}"
            ))

        markup.add(*buttons)

        # Кнопки быстрого перехода
        quick_nav = []
        page_icons = ["📊", "🎮", "🏆"]
        page_names = ["Рейтинги", "Игры", "Турниры"]

        for i in range(1, 4):
            if i == current_page:
                # Текущая страница - неактивная кнопка
                quick_nav.append(types.InlineKeyboardButton(
                    f"• {page_icons[i-1]} •", 
                    callback_data="current_page"
                ))
            else:
                quick_nav.append(types.InlineKeyboardButton(
                    f"{page_icons[i-1]} {page_names[i-1]}", 
                    callback_data=f"profile_page_{i}_{user_id}"
                ))

        markup.add(*quick_nav)

        # Кнопка закрытия
        markup.add(types.InlineKeyboardButton(
            "❌ Закрыть", 
            callback_data="close_profile"
        ))

        return markup
