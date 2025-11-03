from django.utils import timezone


def get_greeting():
    """Возвращает приветствие и эмодзи в зависимости от времени суток"""
    hour = timezone.localtime().hour

    if 5 <= hour < 12:
        return "☀️ Доброе утро"
    elif 12 <= hour < 18:
        return "🌤 Добрый день"
    elif 18 <= hour < 23:
        return "🌇 Добрый вечер"
    else:
        return "🌙 Доброй ночи"
