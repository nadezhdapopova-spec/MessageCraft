import json
import re

from django import forms
from fuzzywuzzy import fuzz


class SpamChecker:
    """Проверяет текстовые поля на запрещённые слова"""

    THRESHOLD = 85
    SPAM_WORDS_PATH = "data/spam_words.json"


    def __init__(self):
        self.spam_words = self._load_spam_words(self.SPAM_WORDS_PATH)
        self.pattern = self._build_pattern(self.spam_words)


    @staticmethod
    def _load_spam_words(filepath: str) -> list:
        """Загружает список запрещённых слов из JSON файла"""
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
            return [word.lower() for word in data.get("spam_words", [])]
        except FileNotFoundError:
            return []


    @staticmethod
    def _build_pattern(words: list):
        """Создаёт паттерн для поиска запрещённых слов"""
        escaped = [re.escape(word) for word in words]
        return re.compile(r'(' + "|".join(escaped) + r')\w*', re.IGNORECASE)


    def check_text(self, text: str) -> None:
        """Проверяет текст на спам и запрещённые слова"""
        if not text:
            return

        text_lower = text.lower()
        found_words = self.pattern.findall(text_lower)
        if found_words:
            unique_words = set(found_words)
            words_str = ", ".join(f"'{w}'" for w in unique_words)
            raise forms.ValidationError(f"Текст содержит запрещённые слова: {words_str}")

        for spam in self.spam_words:
            if fuzz.partial_ratio(spam, text_lower) >= self.THRESHOLD:
                raise forms.ValidationError(f"Текст содержит запрещённое слово: '{spam}'")
