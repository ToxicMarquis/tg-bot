import logging
import pandas as pd
import re
from typing import Dict, Any, Tuple
from telebot import types

logger = logging.getLogger(__name__)

def escape_markdown_v2(text: str) -> str:
    """Экранирование спецсимволов для MarkdownV2"""
    if not text:
        return ""
    escape_chars = r'_*[]()~`>#+=|{}.!'
    return re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', str(text))
    
class MessageFormatter:
    """Форматировщик сообщений для бота"""

    def format_welcome_new(self) -> str:
        """Приветствие для новых пользователей"""
        return """🏁 Добро пожаловать в шахматный бот!

Этот бот поможет вам:
• 📝 Зарегистрироваться в системе
• 👤 Просматривать свой профиль
• 📊 Отслеживать рейтинги Lichess
• 🏆 Следить за турнирными результатами

Для начала нажмите "📝 Регистрация" или введите команду /register"""

    def format_welcome_registered(self, username: str) -> str:
        """Приветствие для зарегистрированных пользователей"""
        return f"""🏁 С возвращением в шахматный бот!

Ваш аккаунт: **{escape_markdown_v2(username)}**

Доступные функции:
• 👤 Просматривать свой профиль
• 📊 Отслеживать рейтинги Lichess  
• 🏆 Следить за турнирными результатами
• 🚪 Выйти из аккаунта (если нужно)"""

    def format_help_message(self, is_developer: bool = False) -> str:
        """Форматирование справочного сообщения"""
        help_text = """🤖 **Доступные команды:**

/start - Запуск бота
/register - Регистрация в системе
/profile - Просмотр профиля
/leaders - Лидерборд команды
/logout - Выход из аккаунта
/stats - Статистика бота
/help - Эта справка

📱 **Кнопки меню:**
📝 Регистрация - Зарегистрироваться в системе
👤 Мой профиль - Посмотреть свой профиль
🏆 Лидерборд команды - Посмотреть лидерборд команды
📊 Статистика - Статистика бота
❓ Помощь - Показать справку
🚪 Выйти из аккаунта - Удалить аккаунт из системы

🔗 **О боте:**
Этот бот интегрируется с Lichess API для получения актуальной информации о рейтингах и статистике игроков.

⚡ **Возможности:**
• Отслеживание рейтингов в различных форматах
• Турнирная статистика"""

        if is_developer:
            help_text += "\n\n🔧 **Команды разработчика:**\n/dev - Меню разработчика"

        return help_text

    def format_stats_message(self, stats_data: Dict[str, Any]) -> str:
        """Форматирование сообщения статистики"""
        return f"""📊 **Статистика бота**

👥 Всего пользователей: {stats_data.get('total_users', 0)}
🟢 Активных за неделю: {stats_data.get('active_users', 0)}
🆕 Новых сегодня: {stats_data.get('new_users_today', 0)}

📈 Активность: {stats_data.get('activity_rate', 0)}%"""

    def format_registration_success(self, username: str) -> str:
        """Сообщение об успешной регистрации"""
        return f"""✅ Успешная регистрация! Ваш Lichess ник: **{escape_markdown_v2(username)}**

Теперь вы можете использовать команду /profile для просмотра своего профиля."""
    
    def format_ratings_page(self, username: str, profile: Dict[str, Any], titles_data: Dict[str, str]) -> str:
        """Форматирование страницы рейтингов (страница 1)"""
        if not profile:
            return "❌ Не удалось получить данные профиля"

        # Звание
        title = f"{titles_data.get(username, '')} "
        lichess_title = profile.get('title', '')
        if lichess_title:
            title = f"{lichess_title} "

        # Рейтинги
        perfs = profile.get('perfs', {})
        ratings = {
            'bullet': perfs.get('bullet', {}),
            'blitz': perfs.get('blitz', {}),
            'rapid': perfs.get('rapid', {}),
            'classical': perfs.get('classical', {}),
            'puzzle': perfs.get('puzzle', {})
        }

        message = f"""
    👤 **{title}{escape_markdown_v2(username)}**

    📊 **Рейтинги Lichess**

    🚀 **Bullet (Пуля):**
       • Рейтинг: {ratings['bullet'].get('rating', 'Нет')}±{ratings['bullet'].get('rd', 'N/A')}
       • Игры: {ratings['bullet'].get('games', 0)}

    ⚡ **Blitz (Блиц):**
       • Рейтинг: {ratings['blitz'].get('rating', 'Нет')}±{ratings['blitz'].get('rd', 'N/A')}
       • Игры: {ratings['blitz'].get('games', 0)}

    🐇 **Rapid (Рапид):**
       • Рейтинг: {ratings['rapid'].get('rating', 'Нет')}±{ratings['rapid'].get('rd', 'N/A')}
       • Игры: {ratings['rapid'].get('games', 0)}

    ⏳ **Classical (Классика):**
       • Рейтинг: {ratings['classical'].get('rating', 'Нет')}±{ratings['classical'].get('rd', 'N/A')}
       • Игры: {ratings['classical'].get('games', 0)}

    🧩 **Puzzles (Задачи):**
       • Рейтинг: {ratings['puzzle'].get('rating', 'Нет')}
       • Решено: {ratings['puzzle'].get('games', 0)}"""
        return message

    def format_games_page(self, username: str, profile: Dict[str, Any]) -> str:
        """Форматирование страницы статистики игр (страница 2)"""
        if not profile:
            return "❌ Не удалось получить данные профиля"

        # Статистика игр
        count = profile.get('count', {})
        total_games = count.get('all', 0)
        wins = count.get('win', 0)
        losses = count.get('loss', 0)
        draws = count.get('draw', 0)

        win_rate = round((wins / total_games * 100), 1) if total_games > 0 else 0

        # Время игры
        play_time = profile.get('playTime', {})
        total_time = play_time.get('total', 0)
        tv_time = play_time.get('tv', 0)

        # Переводим секунды в часы
        total_hours = round(total_time / 3600, 1) if total_time else 0
        tv_hours = round(tv_time / 3600, 1) if tv_time else 0

        message = f"""
    🎮 **{escape_markdown_v2(username)}**

    📈 **Общая статистика игр**

    🔢 **Основные показатели:**
       • Всего игр: {total_games:,}
       • Победы: {wins:,} ({round(wins/total_games*100, 1) if total_games > 0 else 0}%)
       • Поражения: {losses:,} ({round(losses/total_games*100, 1) if total_games > 0 else 0}%)
       • Ничьи: {draws:,} ({round(draws/total_games*100, 1) if total_games > 0 else 0}%)

    📊 **Процент побед:** {win_rate}%

    ⏱️ **Время игры:**
       • Общее время: {total_hours} часов
       • Время на TV: {tv_hours} часов"""
        return message

    def format_logout_warning(self, username: str) -> str:
        """Предупреждение о выходе из аккаунта"""
        return f"""⚠️ **ВНИМАНИЕ!**

Вы собираетесь удалить свой аккаунт из системы.

**Текущий аккаунт:** {escape_markdown_v2(username)}

После удаления:
• Вся ваша информация будет стерта
• Связь с Lichess профилем будет разорвана  
• Вы сможете зарегистрироваться заново

**Вы уверены, что хотите продолжить?**"""

    def format_logout_success(self, username: str) -> str:
        """Сообщение об успешном выходе"""
        return f"""✅ **Аккаунт успешно удален**

Ваш аккаунт **{escape_markdown_v2(username)}** был удален из системы.

Спасибо за использование нашего бота! 
Вы можете зарегистрироваться заново в любое время командой /register"""

    def format_logout_cancel(self) -> str:
        """Сообщение об отмене выхода"""
        return """❌ **Выход отменен**

Ваш аккаунт остается активным. 
Вы можете продолжить пользоваться ботом."""

    def format_developer_menu(self) -> str:
        """Меню разработчика"""
        return """🔧 **Меню разработчика**

Доступные функции:
• 👥 Все пользователи - просмотр списка зарегистрированных пользователей
• 📈 Детальная статистика - подробная статистика активности
• 🗑️ Очистить логи - очистка логов активности
• 💾 Экспорт данных - экспорт всех данных
• 🔄 Перезагрузить данные - перезагрузка системы

Выберите нужную функцию:"""

    def format_all_users(self, users: list[Dict[str, str]]) -> str:
        """Список всех пользователей"""
        if not users:
            return "📝 Пользователи не найдены"
        
        users_text = "👥 **Все зарегистрированные пользователи:**\n\n"
        for i, user in enumerate(users, 1):
            users_text += f"{i}. **[{user['lichess_username']}](https://lichess.org/@/{user['lichess_username']})** (ID: `{user['telegram_id']}`)\n"
            users_text += f"   📅 Регистрация: {user['registration_date']}\n"
            users_text += f"   ⏰ Последняя активность: {user['last_activity']}\n\n"

        return users_text

    def format_detailed_stats(self, users: list[Dict[str, str]], activity_stats: Dict[str, Any]) -> str:
        """Детальная статистика"""
        stats_text = f"""📈 **Детальная статистика бота**

👥 **Пользователи:**
• Всего зарегистрировано: {len(users)}
• Активных за 24 часа: {activity_stats.get('recent_actions', 0)}

📊 **Активность:**
• Всего действий: {activity_stats.get('total_actions', 0)}
• За последние 24 часа: {activity_stats.get('recent_actions', 0)}

🔥 **Популярные действия:**"""

        actions_by_type = activity_stats.get('actions_by_type', {})
        for action, count in sorted(actions_by_type.items(), key=lambda x: x[1], reverse=True):
            stats_text += f"\n• `{action}`: {count}"

        return stats_text

    def format_leaders_page(self, requesting_username: str, tournament_service, page: int = 1) -> Tuple[str, types.InlineKeyboardMarkup]:
        """Форматирование многостраничного лидерборда команды"""
        try:
            # Загружаем турнирные данные
            tournament_data = tournament_service.load_tournament_csv_data()

            if tournament_data.empty:
                message = """🏆 **Лидерборд команды Unicorn7Love Fun Club**

❌ Нет данных о турнирах

💡 **Информация:**
Данные загружаются из CSV файлов турниров.
Обратитесь к администратору для добавления результатов."""

                # Пустая клавиатура для закрытия
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("❌ Закрыть", callback_data="close_leaders"))
                return message, keyboard

            # Фильтруем по команде unicorn7love-fun-club
            team_data = tournament_data[
                tournament_data['team'].str.lower().str.contains('unicorn7love-fun-club', na=False) |
                tournament_data['team'].str.lower().str.contains('unicorn7love', na=False) |
                tournament_data['team'].str.lower().str.contains('fun.club', na=False) |
                tournament_data['team'].str.lower().str.contains('fun-club', na=False)
            ]

            if team_data.empty:
                message = """🏆 **Лидерборд команды Unicorn7Love Fun Club**

❌ Участники команды не найдены"""

                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton("❌ Закрыть", callback_data="close_leaders"))
                return message, keyboard

            # Группируем по игрокам и суммируем очки
            player_stats = team_data.groupby('username').agg({
                'score': 'sum',
                'tournament_date': 'count'  # количество турниров
            }).reset_index()

            player_stats.columns = ['username', 'total_score', 'tournaments_played']

            # Сортируем по очкам (по убыванию)
            player_stats = player_stats.sort_values('total_score', ascending=False).reset_index(drop=True)

            # Вычисляем параметры пагинации
            PLAYERS_PER_PAGE = 10
            total_players = len(player_stats)
            total_pages = (total_players + PLAYERS_PER_PAGE - 1) // PLAYERS_PER_PAGE

            # Проверяем корректность номера страницы
            if page < 1:
                page = 1
            elif page > total_pages:
                page = total_pages

            # Получаем игроков для текущей страницы
            start_idx = (page - 1) * PLAYERS_PER_PAGE
            end_idx = min(start_idx + PLAYERS_PER_PAGE, total_players)
            page_players = player_stats.iloc[start_idx:end_idx]

            # Заголовок
            total_score = player_stats['total_score'].sum()
            message = f"""🏆 **Лидерборд команды
    🦄 Unicorn7Love Fun Club 🦄**

    👥 Участников: {total_players}
    🎯 Всего очков команды: {total_score}
    📄 Страница {page} из {total_pages}

"""

            # Формируем список лидеров для текущей страницы
            requesting_user_position = None
            requesting_user_found_on_page = False

            # Находим позицию запрашивающего пользователя
            for idx, row in player_stats.iterrows():
                if row['username'].lower() == requesting_username.lower():
                    requesting_user_position = idx + 1
                    break

            # Формируем список для текущей страницы
            for local_idx, (_, row) in enumerate(page_players.iterrows()):
                global_position = start_idx + local_idx + 1
                username = escape_markdown_v2(row['username'])
                total_score = row['total_score']
                tournaments = row['tournaments_played']

                # Определяем эмодзи для позиции
                if row['username'].lower() == requesting_username.lower():
                    emoji = "⭐"
                    requesting_user_found_on_page = True
                elif global_position == 1:
                    emoji = "🥇"
                elif global_position == 2:
                    emoji = "🥈"
                elif global_position == 3:
                    emoji = "🥉"
                else:
                    emoji = "⚪"

                # Форматируем строку
                message += f"    {emoji} **{global_position}.** {username} — {total_score} очков ({tournaments} турн.)\n"

            # Если запрашивающий пользователь не на текущей странице, показываем его позицию
            if not requesting_user_found_on_page and requesting_user_position:
                requesting_user_data = player_stats[player_stats['username'].str.lower() == requesting_username.lower()]
                if not requesting_user_data.empty:
                    user_row = requesting_user_data.iloc[0]
                    username_escaped = escape_markdown_v2(user_row['username'])
                    message += f"\n    ...\n    ⭐ **{requesting_user_position}.** {username_escaped} — {user_row['total_score']} очков ({user_row['tournaments_played']} турн.)\n"

            # Добавляем статистику
            if len(player_stats) > 0:
                avg_score = round(player_stats['total_score'].mean(), 1)
                top_scorer = player_stats.iloc[0]
                most_active = player_stats.loc[player_stats['tournaments_played'].idxmax()]

                top_scorer_name = escape_markdown_v2(top_scorer['username'])
                most_active_name = escape_markdown_v2(most_active['username'])

                message += f"""
📊 **Статистика команды:**
    • Средние очки на игрока: {avg_score}
    • Лидер: {top_scorer_name} ({top_scorer['total_score']} очков)
    • Самый активный: {most_active_name} ({player_stats['tournaments_played'].max()} турн.)"""

            # Создаем клавиатуру навигации
            keyboard = self.get_leaders_navigation_keyboard(page, total_pages, requesting_username)

            return message, keyboard

        except Exception as e:
            logger.error(f"Ошибка формирования лидерборда: {e}")
            message = "❌ Ошибка при формировании лидерборда команды"
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("❌ Закрыть", callback_data="close_leaders"))
            return message, keyboard

    def get_leaders_navigation_keyboard(self, current_page: int, total_pages: int, username: str) -> types.InlineKeyboardMarkup:
        """Создание клавиатуры навигации для лидерборда"""
        markup = types.InlineKeyboardMarkup(row_width=3)

        # Кнопки навигации
        nav_buttons = []

        # Кнопка "Назад" (если не первая страница)
        if current_page > 1:
            nav_buttons.append(types.InlineKeyboardButton(
                "◀️ Назад", 
                callback_data=f"leaders_page_{current_page-1}_{username}"
            ))

        # Индикатор текущей страницы
        nav_buttons.append(types.InlineKeyboardButton(
            f"{current_page}/{total_pages}", 
            callback_data="leaders_page_info"
        ))

        # Кнопка "Вперед" (если не последняя страница)
        if current_page < total_pages:
            nav_buttons.append(types.InlineKeyboardButton(
                "Вперед ▶️", 
                callback_data=f"leaders_page_{current_page+1}_{username}"
            ))

        markup.add(*nav_buttons)

        # Кнопки быстрого перехода (если страниц больше 3)
        if total_pages > 3:
            quick_nav = []

            # Первая страница
            if current_page > 2:
                quick_nav.append(types.InlineKeyboardButton(
                    "1️⃣", 
                    callback_data=f"leaders_page_1_{username}"
                ))

            # Средние страницы
            if total_pages > 6 and current_page > 3:
                quick_nav.append(types.InlineKeyboardButton(
                    "...", 
                    callback_data="leaders_page_info"
                ))

            # Последняя страница
            if current_page < total_pages - 1:
                quick_nav.append(types.InlineKeyboardButton(
                    f"{total_pages}️⃣", 
                    callback_data=f"leaders_page_{total_pages}_{username}"
                ))

            if quick_nav:
                markup.add(*quick_nav)

        # Кнопка обновления и закрытия
        markup.add(
            types.InlineKeyboardButton("🔄 Обновить", callback_data=f"leaders_page_{current_page}_{username}"),
            types.InlineKeyboardButton("❌ Закрыть", callback_data="close_leaders")
        )

        return markup
