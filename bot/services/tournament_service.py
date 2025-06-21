import os
import glob
import re
import logging
import pandas as pd
from typing import Optional, List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)


class TournamentService:
    """Сервис для работы с турнирными данными"""

    def __init__(self):
        """Инициализация сервиса турниров"""
        self.tournaments_dir = Config.TOURNAMENTS_DIR

        # Создание директории турниров если не существует
        os.makedirs(self.tournaments_dir, exist_ok=True)

    def load_tournament_csv_data(self,
                                 specific_files: Optional[List[str]] = None
                                 ) -> pd.DataFrame:
        """Загрузка данных турниров из CSV файлов"""
        try:
            all_tournaments = []

            if specific_files:
                csv_files = [
                    os.path.join(self.tournaments_dir, f)
                    if not f.startswith('/') else f for f in specific_files
                ]
            else:
                if os.path.exists(self.tournaments_dir):
                    csv_files = glob.glob(
                        os.path.join(self.tournaments_dir, "*.csv"))
                else:
                    csv_files = glob.glob("*.csv")
                    csv_files = [
                        f for f in csv_files
                        if 'tournament' in f.lower() or 'lichess' in f.lower()
                    ]

            if not csv_files:
                logger.warning(
                    f"Не найдено CSV файлов турниров в {self.tournaments_dir}")
                return pd.DataFrame()

            for csv_file in csv_files:
                try:
                    tournament_df = self._process_tournament_file(csv_file)
                    if not tournament_df.empty:
                        all_tournaments.append(tournament_df)

                except Exception as e:
                    logger.error(f"Ошибка загрузки файла {csv_file}: {e}")
                    continue

            if all_tournaments:
                combined_df = pd.concat(all_tournaments, ignore_index=True)
                logger.info(
                    f"Загружено {len(combined_df)} записей из {len(all_tournaments)} турниров"
                )
                return combined_df
            else:
                logger.warning("Не удалось загрузить ни одного турнира")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Ошибка загрузки турнирных данных: {e}")
            return pd.DataFrame()

    def _process_tournament_file(self, csv_file: str) -> pd.DataFrame:
        """Обработка одного файла турнира"""
        try:
            # Загружаем данные турнира
            tournament_df = pd.read_csv(csv_file)

            # Добавляем информацию о файле/турнире
            tournament_name = os.path.basename(csv_file).replace('.csv', '')
            tournament_df['tournament_file'] = tournament_name

            # Извлекаем дату из названия файла
            date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', tournament_name)
            if date_match:
                tournament_df['tournament_date'] = date_match.group(1)
            else:
                tournament_df['tournament_date'] = 'Unknown'

            # Стандартизируем названия колонок
            column_mapping = {
                'Rank': 'rank',
                'Title': 'title',
                'Username': 'username',
                'Rating': 'rating',
                'Score': 'score',
                'Performance': 'performance',
                'Team': 'team'
            }

            tournament_df = tournament_df.rename(columns=column_mapping)
            tournament_df = tournament_df.dropna(subset=['username'])

            logger.info(
                f"Загружен турнир из {csv_file}: {len(tournament_df)} участников"
            )
            return tournament_df

        except Exception as e:
            logger.error(f"Ошибка обработки файла {csv_file}: {e}")
            return pd.DataFrame()

    def get_user_tournament_stats(
            self, username: str,
            tournament_data: pd.DataFrame) -> Dict[str, Any]:
        """Получение статистики пользователя по турнирам"""
        if tournament_data.empty:
            return {}

        try:
            # Фильтруем данные по пользователю
            user_data = tournament_data[
                tournament_data['username'].str.lower() == username.lower()]

            if user_data.empty:
                return {}

            # Вычисляем статистику
            stats = {
                'tournaments_played':
                len(user_data),
                'best_rank':
                user_data['rank'].min()
                if 'rank' in user_data.columns else None,
                'average_rank':
                round(user_data['rank'].mean(), 1)
                if 'rank' in user_data.columns else None,
                'total_score':
                user_data['score'].sum()
                if 'score' in user_data.columns else None,
                'average_score':
                round(user_data['score'].mean(), 1)
                if 'score' in user_data.columns else None,
                'best_performance':
                user_data['performance'].max()
                if 'performance' in user_data.columns else None,
                'average_performance':
                round(user_data['performance'].mean(), 1)
                if 'performance' in user_data.columns
                and user_data['performance'].notna().any() else None,
                'recent_tournaments':
                user_data[[
                    'tournament_date', 'rank', 'score', 'performance'
                ]].tail(3).to_dict('records') if len(user_data) > 0 else []
            }

            return stats

        except Exception as e:
            logger.error(
                f"Ошибка получения турнирной статистики для {username}: {e}")
            return {}

    def format_tournaments_page(self, username: str,
                                tournament_data: pd.DataFrame) -> str:
        """Форматирование страницы турнирной статистики (страница 3)"""
        tournament_stats = self.get_user_tournament_stats(
            username, tournament_data)

        if not tournament_stats:
            message = f"""
    🏆 **{username}**

    📋 **Турнирная статистика**

    ❌ Данные о турнирах отсутствуют

    💡 **Информация:**
    Если Вы нашли ошибку, пожалуйста, обратитесь к [администратору](https://t.me/mrmarqu1s).
    """
            return message

        # Последние турниры
        recent = tournament_stats.get('recent_tournaments', [])
        recent_text = ""
        if recent:
            recent_text = "\n📅 **Последние турниры:**\n"
            for i, tournament in enumerate(recent[-3:], 1):
                recent_text += f"   {i}. {tournament.get('tournament_date', 'N/A')} - "
                recent_text += f"Место: {tournament.get('rank', 'N/A')}, "
                recent_text += f"Очки: {tournament.get('score', 'N/A')}\n"

        message = f"""
    🏆 **{username}**

    🏟️ **Турнирная статистика**

    📊 **Основные показатели:**
       • Турниров сыграно: {tournament_stats.get('tournaments_played', 0)}
       • Лучшее место: {tournament_stats.get('best_rank', 'N/A')}
       • Среднее место: {tournament_stats.get('average_rank', 'N/A')}

    💯 **Очки:**
       • Всего очков: {tournament_stats.get('total_score', 'N/A')}
       • Средние очки: {tournament_stats.get('average_score', 'N/A')}

    ⚡ **Performance:**
       • Лучший: {tournament_stats.get('best_performance', 'N/A')}
       • Средний: {tournament_stats.get('average_performance', 'N/A')}

    {recent_text}
    """
        return message
