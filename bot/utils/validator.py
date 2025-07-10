import re
from typing import Tuple

class Validator:
    """
    Класс Validator отвечает за проверку и валидацию пользовательского ввода:
    - validate_username: проверка никнейма
    - validate_bio_flag: проверка наличия фразы "univerify" в описании
    - sanitize_text: очистка текста от потенциально вредоносных паттернов
    """

    # Шаблон для допустимых символов в username: латинские буквы, цифры, подчеркивание
    USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_]{3,20}$')
    # Список ключевых SQL/XSS-паттернов для фильтрации
    FORBIDDEN_PATTERNS = [
        r'<\s*script',    # XSS
        r'eval\s*\(',     # JS eval
        r'select\s+',     # SQL
        r'insert\s+',     # SQL
        r'delete\s+',     # SQL
        r'update\s+',     # SQL
        r'--',            # SQL comment
        r';',             # SQL delimiter
    ]

    @classmethod
    def validate_username(cls, username: str) -> Tuple[bool, str]:
        """
        Проверяет username на соответствие требованиям:
        - длина 3–20 символов
        - только латинские буквы, цифры и _
        - отсутствие SQL/XSS паттернов
        Возвращает (True, "") если ок, иначе (False, причина).
        """
        if not username:
            return False, "Username не может быть пустым."
        if not cls.USERNAME_PATTERN.match(username):
            return False, (
                "Никнейм должен содержать только латинские буквы, цифры или "
                "подчеркивания и быть длиной от 3 до 20 символов."
            )
        low = username.lower()
        for pat in cls.FORBIDDEN_PATTERNS:
            if re.search(pat, low):
                return False, "Никнейм содержит запрещенные символы или паттерны."
        return True, ""

    @staticmethod
    def validate_bio_flag(bio: str) -> Tuple[bool, str]:
        """
        Проверяет, что в описании пользователя (bio) присутствует слово "univerify".
        Не чувствительно к регистру.
        """
        if not bio:
            return False, "Описание профиля не задано."
        if "univerify" not in bio.lower():
            return False, 'В описание профиля необходимо добавить слово "univerify".'
        return True, ""

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Очищает входящий текст от опасных SQL/XSS-паттернов,
        заменяя их на безопасные экранированные аналоги.
        """
        safe = text
        # экранировать угловые скобки для XSS
        safe = safe.replace("<", "&lt;").replace(">", "&gt;")
        # удалить точку с запятой и двойные дефисы
        safe = re.sub(r';', '', safe)
        safe = re.sub(r'--', '', safe)
        # убрать ключевые SQL-операторы
        for pat in cls.FORBIDDEN_PATTERNS:
            safe = re.sub(pat, '', safe, flags=re.IGNORECASE)
        return safe
