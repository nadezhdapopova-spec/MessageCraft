from django.core.cache import cache

CACHE_TIMEOUT = 60 * 15


def safe_delete_pattern(pattern):
    """Безопасное удаление по шаблону для разных backends"""
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(pattern)
    else:
        cache.clear()
