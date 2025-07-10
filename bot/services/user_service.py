import json
import logging
import os
import re
import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import csv
import requests
from dataclasses import dataclass

@dataclass
class UserProfile:
    """Класс для представления профиля пользователя"""
    username: str
    telegram_id: int
    level: int
    xp: int
    required_xp: int
    coins: int
    title: Optional[str] = None
    lichess_ratings: Optional[Dict[str, int]] = None
    stats: Optional[Dict[str, Any]] = None
    app_data: Optional[Dict[str, Any]] = None

class UserService:
    """
    Сервис для управления пользователями Telegram Chess Bot

    Функции:
    - Регистрация и валидация пользователей
    - Система уровней и опыта
    - Управление профилями
    - Магазин и кастомизация
    - Интеграция с турнирными данными
    """

    def __init__(self):
        self.data_dir = "data"
        self.users_file = os.path.join(self.data_dir, "users.txt")
        self.activity_file = os.path.join(self.data_dir, "activity.txt")
        self.titles_file = os.path.join(self.data_dir, "titles.json")
        self.app_db_file = os.path.join(self.data_dir, "app_db.json")

        # Создаем директорию данных, если её нет
        os.makedirs(self.data_dir, exist_ok=True)

        # Настройка логирования
        self.logger = logging.getLogger(__name__)

        # Инициализация файлов
        self._init_files()

    def _init_files(self):
        """Инициализация файлов данных"""
        try:
            # Создаем файл пользователей, если его нет
            if not os.path.exists(self.users_file):
                with open(self.users_file, 'w', encoding='utf-8') as f:
                    f.write("# Пользователи бота\n")

            # Создаем файл активности, если его нет
            if not os.path.exists(self.activity_file):
                with open(self.activity_file, 'w', encoding='utf-8') as f:
                    f.write("# Логи активности\n")

            # Создаем файл титулов, если его нет
            if not os.path.exists(self.titles_file):
                with open(self.titles_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)

            # Создаем файл данных приложения, если его нет
            if not os.path.exists(self.app_db_file):
                with open(self.app_db_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"Ошибка инициализации файлов: {e}")

    def validate_username(self, username: str) -> Tuple[bool, str]:
        """
        Валидация никнейма пользователя

        Проверки:
        - Длина от 3 до 20 символов
        - Только латинские буквы, цифры и подчеркивания
        - Защита от SQL-инъекций
        - Фильтрация запрещенных паттернов
        """
        try:
            # Проверка на пустоту
            if not username or not username.strip():
                return False, "Никнейм не может быть пустым"

            username = username.strip()

            # Проверка длины
            if len(username) < 3 or len(username) > 20:
                return False, "Никнейм должен быть от 3 до 20 символов"

            # Проверка на допустимые символы
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                return False, "Никнейм может содержать только буквы, цифры и подчеркивания"

            # Защита от SQL-инъекций и XSS
            dangerous_patterns = [
                r'(select|insert|update|delete|drop|create|alter|exec|union)',
                r'(script|javascript|vbscript|onload|onerror)',
                r'(--|;|/\*|\*/|<|>|&|\|)',
                r'(null|admin|root|test|guest)'
            ]

            username_lower = username.lower()
            for pattern in dangerous_patterns:
                if re.search(pattern, username_lower, re.IGNORECASE):
                    return False, "Никнейм содержит запрещенные символы или слова"

            return True, "Никнейм корректен"

        except Exception as e:
            self.logger.error(f"Ошибка валидации никнейма {username}: {e}")
            return False, "Ошибка валидации никнейма"

    def is_user_registered(self, telegram_id: int = None, username: str = None) -> bool:
        """Проверка регистрации пользователя"""
        try:
            if not os.path.exists(self.users_file):
                return False

            with open(self.users_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        stored_username = parts[0]
                        stored_telegram_id = int(parts[1]) if parts[1].isdigit() else None

                        if telegram_id and stored_telegram_id == telegram_id:
                            return True
                        if username and stored_username == username:
                            return True

            return False

        except Exception as e:
            self.logger.error(f"Ошибка проверки регистрации: {e}")
            return False

    def register_user(self, telegram_id: int, username: str, bio_check: bool = True) -> Tuple[bool, str]:
        """
        Регистрация нового пользователя

        Args:
            telegram_id: ID пользователя в Telegram
            username: Никнейм пользователя
            bio_check: Проверка наличия 'univerify' в био
        """
        try:
            # Проверка валидности никнейма
            is_valid, message = self.validate_username(username)
            if not is_valid:
                return False, message

            # Проверка на существование пользователя
            if self.is_user_registered(telegram_id=telegram_id):
                return False, "Пользователь уже зарегистрирован"

            if self.is_user_registered(username=username):
                return False, "Никнейм уже занят"

            # Проверка bio (если требуется)
            if bio_check:
                # Здесь должна быть проверка через Telegram API
                # Для демонстрации пропускаем, в реальности нужно проверить био
                pass

            # Добавляем пользователя в файл
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_data = f"{username}|{telegram_id}|{timestamp}|0|0\n"

            with open(self.users_file, 'a', encoding='utf-8') as f:
                f.write(user_data)

            # Логируем активность
            self._log_activity(username, "registration", f"Зарегистрирован пользователь {username}")

            # Инициализируем данные приложения
            self._init_user_app_data(username)

            return True, "Пользователь успешно зарегистрирован"

        except Exception as e:
            self.logger.error(f"Ошибка регистрации пользователя {username}: {e}")
            return False, "Ошибка регистрации пользователя"

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получение данных пользователя по никнейму"""
        try:
            if not os.path.exists(self.users_file):
                return None

            with open(self.users_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split('|')
                    if len(parts) >= 4 and parts[0] == username:
                        return {
                            'username': parts[0],
                            'telegram_id': int(parts[1]) if parts[1].isdigit() else None,
                            'registration_date': parts[2],
                            'coins': int(parts[3]) if parts[3].isdigit() else 0,
                            'games_won': int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                        }

            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения пользователя {username}: {e}")
            return None

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение данных пользователя по Telegram ID"""
        try:
            if not os.path.exists(self.users_file):
                return None

            with open(self.users_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split('|')
                    if len(parts) >= 2 and parts[1] == str(telegram_id):
                        return {
                            'username': parts[0],
                            'telegram_id': int(parts[1]),
                            'registration_date': parts[2] if len(parts) > 2 else None,
                            'coins': int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0,
                            'games_won': int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                        }

            return None

        except Exception as e:
            self.logger.error(f"Ошибка получения пользователя по ID {telegram_id}: {e}")
            return None

    def calculate_level_and_xp(self, points: int = 0, attendance: int = 0, avg_performance: float = 0.0) -> Tuple[int, int, int]:
        """
        Расчет уровня и опыта по формулам из ТЗ

        Формула опыта: Очки × 10 + Посещаемость × 25 + Средний перформанс ÷ 100
        Формула уровня: 50 × 1.5^(n-1)

        Returns:
            Tuple[уровень, текущий_опыт, требуемый_опыт_для_следующего_уровня]
        """
        try:
            # Расчет текущего опыта
            current_xp = int(points * 10 + attendance * 25 + avg_performance / 100)

            # Определяем уровень
            level = 0
            total_xp_needed = 0

            while total_xp_needed <= current_xp:
                level += 1
                level_xp = int(50 * (1.5 ** (level - 1)))
                total_xp_needed += level_xp

            # Корректируем, если превысили
            if total_xp_needed > current_xp:
                level -= 1
                if level > 0:
                    total_xp_needed -= int(50 * (1.5 ** (level - 1)))

            # Рассчитываем опыт для следующего уровня
            next_level_xp = int(50 * (1.5 ** level)) if level > 0 else 50

            return max(0, level), current_xp, next_level_xp

        except Exception as e:
            self.logger.error(f"Ошибка расчета уровня: {e}")
            return 0, 0, 50

    def get_tournament_stats(self, username: str) -> Dict[str, Any]:
        """Получение статистики из турнирных данных"""
        try:
            stats = {
                'points': 0,
                'attendance': 0,
                'avg_performance': 0.0,
                'tournaments_played': 0
            }

            # Ищем CSV файлы турниров
            tournament_dir = "tournaments"
            if not os.path.exists(tournament_dir):
                return stats

            total_performance = 0
            performance_count = 0

            for filename in os.listdir(tournament_dir):
                if filename.endswith('.csv'):
                    filepath = os.path.join(tournament_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                if row.get('username', '').lower() == username.lower():
                                    stats['tournaments_played'] += 1
                                    stats['attendance'] += 1

                                    # Добавляем очки
                                    points = float(row.get('points', 0))
                                    stats['points'] += points

                                    # Добавляем перформанс
                                    performance = float(row.get('performance', 0))
                                    if performance > 0:
                                        total_performance += performance
                                        performance_count += 1

                    except Exception as e:
                        self.logger.error(f"Ошибка чтения турнира {filename}: {e}")

            # Рассчитываем средний перформанс
            if performance_count > 0:
                stats['avg_performance'] = total_performance / performance_count

            return stats

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики турниров для {username}: {e}")
            return {'points': 0, 'attendance': 0, 'avg_performance': 0.0, 'tournaments_played': 0}

    def get_lichess_ratings(self, username: str) -> Dict[str, int]:
        """Получение рейтингов с Lichess API"""
        try:
            # Получаем токен из переменных окружения
            lichess_token = os.getenv('LICHESS_TOKEN')
            if not lichess_token:
                self.logger.warning("Отсутствует токен Lichess")
                return {'bullet': 0, 'blitz': 0, 'rapid': 0, 'classical': 0}

            # Делаем запрос к API Lichess
            headers = {'Authorization': f'Bearer {lichess_token}'}
            response = requests.get(f'https://lichess.org/api/user/{username}', headers=headers)

            if response.status_code == 200:
                data = response.json()
                perfs = data.get('perfs', {})

                ratings = {}
                for time_control in ['bullet', 'blitz', 'rapid', 'classical']:
                    rating_data = perfs.get(time_control, {})
                    ratings[time_control] = rating_data.get('rating', 0)

                return ratings
            else:
                self.logger.warning(f"Ошибка API Lichess: {response.status_code}")
                return {'bullet': 0, 'blitz': 0, 'rapid': 0, 'classical': 0}

        except Exception as e:
            self.logger.error(f"Ошибка получения рейтингов Lichess для {username}: {e}")
            return {'bullet': 0, 'blitz': 0, 'rapid': 0, 'classical': 0}

    def get_user_profile(self, username: str) -> Optional[UserProfile]:
        """Получение полного профиля пользователя"""
        try:
            user_data = self.get_user_by_username(username)
            if not user_data:
                return None

            # Получаем статистику турниров
            tournament_stats = self.get_tournament_stats(username)

            # Рассчитываем уровень и опыт
            level, current_xp, required_xp = self.calculate_level_and_xp(
                points=tournament_stats['points'],
                attendance=tournament_stats['attendance'],
                avg_performance=tournament_stats['avg_performance']
            )

            # Получаем рейтинги Lichess
            lichess_ratings = self.get_lichess_ratings(username)

            # Получаем титул
            title = self.get_user_title(username)

            # Получаем данные приложения
            app_data = self.get_app_data(username)

            return UserProfile(
                username=username,
                telegram_id=user_data['telegram_id'],
                level=level,
                xp=current_xp,
                required_xp=required_xp,
                coins=user_data.get('coins', 0),
                title=title,
                lichess_ratings=lichess_ratings,
                stats=tournament_stats,
                app_data=app_data
            )

        except Exception as e:
            self.logger.error(f"Ошибка получения профиля {username}: {e}")
            return None

    def calculate_utility_coefficient(self, points: int, attendance: int, avg_performance: float) -> int:
        """
        Расчет коэффициента полезности
        Формула: 1,000,000 × очки + 1,000 × посещаемость + средний перформанс
        """
        try:
            return int(1000000 * points + 1000 * attendance + avg_performance)
        except Exception as e:
            self.logger.error(f"Ошибка расчета коэффициента полезности: {e}")
            return 0

    def get_leaderboard(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение таблицы лидеров"""
        try:
            if not os.path.exists(self.users_file):
                return []

            leaderboard = []

            with open(self.users_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        username = parts[0]

                        # Получаем статистику
                        stats = self.get_tournament_stats(username)

                        # Рассчитываем коэффициент полезности
                        utility = self.calculate_utility_coefficient(
                            points=stats['points'],
                            attendance=stats['attendance'],
                            avg_performance=stats['avg_performance']
                        )

                        # Получаем уровень
                        level, xp, _ = self.calculate_level_and_xp(
                            points=stats['points'],
                            attendance=stats['attendance'],
                            avg_performance=stats['avg_performance']
                        )

                        leaderboard.append({
                            'username': username,
                            'level': level,
                            'xp': xp,
                            'utility_coefficient': utility,
                            'points': stats['points'],
                            'attendance': stats['attendance'],
                            'avg_performance': stats['avg_performance'],
                            'title': self.get_user_title(username)
                        })

            # Сортируем по коэффициенту полезности
            leaderboard.sort(key=lambda x: x['utility_coefficient'], reverse=True)

            return leaderboard[:limit]

        except Exception as e:
            self.logger.error(f"Ошибка получения таблицы лидеров: {e}")
            return []

    def get_user_title(self, username: str) -> Optional[str]:
        """Получение неофициального титула пользователя"""
        try:
            with open(self.titles_file, 'r', encoding='utf-8') as f:
                titles = json.load(f)

            return titles.get(username)

        except Exception as e:
            self.logger.error(f"Ошибка получения титула для {username}: {e}")
            return None

    def set_user_title(self, username: str, title: str) -> bool:
        """Установка неофициального титула пользователя"""
        try:
            with open(self.titles_file, 'r', encoding='utf-8') as f:
                titles = json.load(f)

            titles[username] = title

            with open(self.titles_file, 'w', encoding='utf-8') as f:
                json.dump(titles, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Ошибка установки титула для {username}: {e}")
            return False

    def _init_user_app_data(self, username: str):
        """Инициализация данных приложения для нового пользователя"""
        try:
            with open(self.app_db_file, 'r', encoding='utf-8') as f:
                app_data = json.load(f)

            if username not in app_data:
                app_data[username] = {
                    'background': None,
                    'avatar': None,
                    'banner': None,
                    'avatar_effect': 0,
                    'profile_effect': 0
                }

                with open(self.app_db_file, 'w', encoding='utf-8') as f:
                    json.dump(app_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"Ошибка инициализации данных приложения для {username}: {e}")

    def get_app_data(self, username: str) -> Dict[str, Any]:
        """Получение данных приложения пользователя"""
        try:
            with open(self.app_db_file, 'r', encoding='utf-8') as f:
                app_data = json.load(f)

            return app_data.get(username, {
                'background': None,
                'avatar': None,
                'banner': None,
                'avatar_effect': 0,
                'profile_effect': 0
            })

        except Exception as e:
            self.logger.error(f"Ошибка получения данных приложения для {username}: {e}")
            return {
                'background': None,
                'avatar': None,
                'banner': None,
                'avatar_effect': 0,
                'profile_effect': 0
            }

    def update_app_data(self, username: str, data: Dict[str, Any]) -> bool:
        """Обновление данных приложения пользователя"""
        try:
            with open(self.app_db_file, 'r', encoding='utf-8') as f:
                app_data = json.load(f)

            if username not in app_data:
                app_data[username] = {}

            app_data[username].update(data)

            with open(self.app_db_file, 'w', encoding='utf-8') as f:
                json.dump(app_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            self.logger.error(f"Ошибка обновления данных приложения для {username}: {e}")
            return False

    def can_purchase_item(self, username: str, item_cost: int, required_level: int) -> Tuple[bool, str]:
        """Проверка возможности покупки товара"""
        try:
            user_data = self.get_user_by_username(username)
            if not user_data:
                return False, "Пользователь не найден"

            # Получаем статистику для расчета уровня
            stats = self.get_tournament_stats(username)
            level, _, _ = self.calculate_level_and_xp(
                points=stats['points'],
                attendance=stats['attendance'],
                avg_performance=stats['avg_performance']
            )

            # Проверяем уровень
            if level < required_level:
                return False, f"Требуется {required_level} уровень (у вас {level})"

            # Проверяем монеты
            coins = user_data.get('coins', 0)
            if coins < item_cost:
                return False, f"Недостаточно монет (нужно {item_cost}, у вас {coins})"

            return True, "Покупка доступна"

        except Exception as e:
            self.logger.error(f"Ошибка проверки покупки для {username}: {e}")
            return False, "Ошибка проверки"

    def purchase_item(self, username: str, item_type: str, item_cost: int, required_level: int, item_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Покупка товара в магазине"""
        try:
            # Проверяем возможность покупки
            can_purchase, message = self.can_purchase_item(username, item_cost, required_level)
            if not can_purchase:
                return False, message

            # Списываем монеты
            success = self.add_coins(username, -item_cost)
            if not success:
                return False, "Ошибка списания монет"

            # Обновляем данные приложения
            success = self.update_app_data(username, item_data)
            if not success:
                # Возвращаем монеты обратно
                self.add_coins(username, item_cost)
                return False, "Ошибка обновления данных"

            # Логируем покупку
            self._log_activity(username, "purchase", f"Куплен {item_type} за {item_cost} монет")

            return True, "Товар успешно куплен"

        except Exception as e:
            self.logger.error(f"Ошибка покупки для {username}: {e}")
            return False, "Ошибка покупки"

    def add_coins(self, username: str, amount: int) -> bool:
        """Добавление монет пользователю"""
        try:
            # Читаем файл пользователей
            with open(self.users_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Обновляем данные пользователя
            updated_lines = []
            user_found = False

            for line in lines:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split('|')
                    if len(parts) >= 2 and parts[0] == username:
                        user_found = True
                        current_coins = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
                        new_coins = max(0, current_coins + amount)

                        # Обновляем строку
                        parts[3] = str(new_coins)
                        updated_lines.append('|'.join(parts) + '\n')
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)

            if not user_found:
                return False

            # Записываем обновленные данные
            with open(self.users_file, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)

            return True

        except Exception as e:
            self.logger.error(f"Ошибка добавления монет для {username}: {e}")
            return False

    def _log_activity(self, username: str, activity_type: str, description: str):
        """Логирование активности пользователя"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {username} | {activity_type} | {description}\n"

            with open(self.activity_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)

        except Exception as e:
            self.logger.error(f"Ошибка логирования активности: {e}")

    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """Получение полной статистики пользователя"""
        try:
            user_data = self.get_user_by_username(username)
            if not user_data:
                return {}

            tournament_stats = self.get_tournament_stats(username)
            level, xp, required_xp = self.calculate_level_and_xp(
                points=tournament_stats['points'],
                attendance=tournament_stats['attendance'],
                avg_performance=tournament_stats['avg_performance']
            )

            return {
                'basic_info': user_data,
                'tournament_stats': tournament_stats,
                'level_info': {
                    'level': level,
                    'current_xp': xp,
                    'required_xp': required_xp
                },
                'lichess_ratings': self.get_lichess_ratings(username),
                'title': self.get_user_title(username),
                'app_data': self.get_app_data(username)
            }

        except Exception as e:
            self.logger.error(f"Ошибка получения статистики для {username}: {e}")
            return {}

    def get_all_users(self) -> List[str]:
        """Получение списка всех пользователей"""
        try:
            users = []

            with open(self.users_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                if line.strip() and not line.startswith('#'):
                    parts = line.strip().split('|')
                    if len(parts) >= 1:
                        users.append(parts[0])

            return users

        except Exception as e:
            self.logger.error(f"Ошибка получения списка пользователей: {e}")
            return []

    def update_user_coins_from_game(self, username: str, difficulty_level: int, won: bool) -> int:
        """Обновление монет после игры в шахматы"""
        try:
            if not won:
                return 0

            # Расчет монет в зависимости от уровня сложности
            coins_table = {
                1: 5,   # 1250 ELO
                2: 7,   # 1500 ELO
                3: 10,  # 1750 ELO
                4: 15,  # 2000 ELO
                5: 20   # 2250 ELO
            }

            coins_earned = coins_table.get(difficulty_level, 5)

            # Добавляем монеты
            if self.add_coins(username, coins_earned):
                self._log_activity(username, "chess_win", f"Заработано {coins_earned} монет за победу на уровне {difficulty_level}")
                return coins_earned

            return 0

        except Exception as e:
            self.logger.error(f"Ошибка обновления монет после игры для {username}: {e}")
            return 0
