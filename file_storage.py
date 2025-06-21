import os
import csv
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class FileStorageService:
    """Сервис для работы с файловым хранилищем данных"""

    DEVELOPER_ID = Config.DEVELOPER_ID
    def __init__(self):
        """Инициализация файлового хранилища"""
        self.users_file = Config.USERS_FILE
        self.activity_file = Config.ACTIVITY_FILE
        self.titles_file = Config.TITLES_FILE
        self.init_text_storage()

    def init_text_storage(self):
        """Инициализация текстовых файлов для хранения данных"""
        try:
            # Создание директорий
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            os.makedirs(os.path.dirname(self.activity_file), exist_ok=True)

            # Создание файла пользователей
            if not os.path.exists(self.users_file):
                with open(self.users_file, 'w', encoding='utf-8') as f:
                    f.write("telegram_id,lichess_username,registration_date,last_activity,notification_enabled\n")
                logger.info(f"Создан файл пользователей: {self.users_file}")

            # Создание файла активности
            if not os.path.exists(self.activity_file):
                with open(self.activity_file, 'w', encoding='utf-8') as f:
                    f.write("telegram_id,action,timestamp\n")
                logger.info(f"Создан файл активности: {self.activity_file}")

            # Создание директории турниров
            os.makedirs(Config.TOURNAMENTS_DIR, exist_ok=True)

            logger.info("Система текстового хранения инициализирована")

        except Exception as e:
            logger.error(f"Ошибка инициализации текстового хранения: {e}")
            raise

    def get_user_from_file(self, telegram_id: int) -> Optional[str]:
        """Получить пользователя из файла"""
        try:
            if not os.path.exists(self.users_file):
                return None

            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if int(row['telegram_id']) == telegram_id:
                        self.update_user_activity(telegram_id)
                        return row['lichess_username']

            return None

        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None

    def update_user_activity(self, telegram_id: int):
        """Обновить время последней активности пользователя"""
        try:
            lines = []
            updated = False
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                lines.append(headers)

                for row in reader:
                    if int(row[0]) == telegram_id:
                        row[3] = current_time  # Обновляем last_activity
                        updated = True
                    lines.append(row)

            if updated:
                with open(self.users_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(lines)

        except Exception as e:
            logger.error(f"Ошибка обновления активности: {e}")

    def register_user(self, telegram_id: int, lichess_username: str) -> bool:
        """Регистрация нового пользователя"""
        try:
            # Проверяем, существует ли уже пользователь
            if self.get_user_from_file(telegram_id):
                return False

            # Проверяем уникальность никнейма
            with open(self.users_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['lichess_username'].lower() == lichess_username.lower():
                        return False

            # Добавляем нового пользователя
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.users_file, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([telegram_id, lichess_username, current_time, current_time, True])

            self.log_activity(telegram_id, 'registration')
            logger.info(f"Пользователь {lichess_username} зарегистрирован")
            return True

        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")
            return False

    def delete_user_from_storage(self, telegram_id: int) -> bool:
        """Удаление пользователя из файлового хранилища"""
        try:
            updated_users = []
            user_found = False

            with open(self.users_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader)
                updated_users.append(header)

                for row in reader:
                    if len(row) > 0 and str(row[0]) != str(telegram_id):
                        updated_users.append(row)
                    elif str(row[0]) == str(telegram_id):
                        user_found = True

            if not user_found:
                return False

            # Перезаписываем файл без удаленного пользователя
            with open(self.users_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(updated_users)

            self.log_activity(telegram_id, 'account_deletion')
            logger.info(f"Пользователь {telegram_id} удален из системы")
            return True

        except Exception as e:
            logger.error(f"Ошибка удаления пользователя: {e}")
            return False
    
    def log_activity(self, telegram_id: int, action: str):
        """Логирование активности пользователя"""
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.activity_file, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([telegram_id, action, current_time])

        except Exception as e:
            logger.error(f"Ошибка логирования активности: {e}")

    def get_all_users(self) -> List[Dict[str, str]]:
        """Получить всех пользователей"""
        try:
            users = []
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    users = list(reader)
            return users

        except Exception as e:
            logger.error(f"Ошибка получения всех пользователей: {e}")
            return []

    def get_activity_stats(self) -> Dict[str, Any]:
        """Получить статистику активности"""
        try:
            stats = {
                'total_actions': 0,
                'recent_actions': 0,
                'actions_by_type': {}
            }

            if os.path.exists(self.activity_file):
                with open(self.activity_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        stats['total_actions'] += 1
                        action = row['action']
                        stats['actions_by_type'][action] = stats['actions_by_type'].get(action, 0) + 1

                        # Проверяем активность за последние 24 часа
                        try:
                            action_time = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                            if (datetime.now() - action_time).days < 1:
                                stats['recent_actions'] += 1
                        except:
                            pass

            return stats

        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}

    def clear_activity_logs(self) -> bool:
        """Очистить логи активности"""
        try:
            with open(self.activity_file, 'w', encoding='utf-8') as f:
                f.write("telegram_id,action,timestamp\n")
            logger.info("Логи активности очищены")
            return True

        except Exception as e:
            logger.error(f"Ошибка очистки логов: {e}")
            return False

    def load_titles_from_file(self) -> Dict[str, str]:
        """Загрузка званий из файла"""
        try:
            import json
            with open(self.titles_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        except FileNotFoundError:
            logger.warning(f"Файл {self.titles_file} не найден")
            return {}

        except Exception as e:
            logger.error(f"Ошибка загрузки файла званий: {e}")
            return {}

    def get_basic_stats(self) -> Dict[str, Any]:
        """Получить базовую статистику"""
        try:
            users = self.get_all_users()
            total_users = len(users)

            # Подсчет активных пользователей за последние 7 дней
            active_users = 0
            new_users_today = 0
            current_date = datetime.now().strftime('%Y-%m-%d')

            for user in users:
                try:
                    last_activity = datetime.strptime(user['last_activity'], '%Y-%m-%d %H:%M:%S')
                    if (datetime.now() - last_activity).days <= 7:
                        active_users += 1

                    reg_date = datetime.strptime(user['registration_date'], '%Y-%m-%d %H:%M:%S')
                    if reg_date.strftime('%Y-%m-%d') == current_date:
                        new_users_today += 1
                except:
                    pass

            return {
                'total_users': total_users,
                'active_users': active_users,
                'new_users_today': new_users_today,
                'activity_rate': round(active_users/total_users*100, 1) if total_users > 0 else 0
            }

        except Exception as e:
            logger.error(f"Ошибка получения базовой статистики: {e}")
            return {}
