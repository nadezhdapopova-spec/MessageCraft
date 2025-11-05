import re

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet, Q
from django.http import Http404

from mailings.models import Mailing


CACHE_TIMEOUT = 60 * 15


def is_moderator(user):
    """Проверяет, состоит ли пользователь в группе модераторов"""
    return user.is_superuser or user.groups.filter(name="moderator").exists()


def get_visible_mailings_for_user(user):
    """
    Если пользователь авторизован, возвращает список его сообщений.
    Если пользователь - модератор, возвращает список всех сообщений
    """
    if not user.is_authenticated:
        return Mailing.objects.none()
    if is_moderator(user):
        return Mailing.objects.select_related("owner").order_by("owner")
    return Mailing.objects.filter(owner=user)


def get_cached_mailings(user, timeout=CACHE_TIMEOUT):
    """Возвращает кэшированный список сообщений с учётом прав пользователя"""
    user_type = (
        "moderator" if is_moderator(user)
        else "owner" if user.is_authenticated
        else "anon"
    )
    cache_key = f"mailings_user_{user_type}_{user.pk if user.is_authenticated else 'anon'}"
    queryset = cache.get(cache_key)
    if queryset is not None:
        return queryset

    queryset = get_visible_mailings_for_user(user)
    queryset = queryset.select_related("owner")
    cache.set(cache_key, queryset, timeout)
    return queryset


def can_user_view_mail(user, mail):
    """
        Проверяет, имеет ли пользователь право просматривать сообщения.
        Возбуждается Http404: 'Информация недоступна', если доступ запрещён
        """
    if not user.is_authenticated:
        raise Http404("Информация недоступна")
    else:
        if not is_moderator and mail.owner != user:
            raise Http404("Информация недоступна")


def safe_delete_pattern(pattern):
    """Безопасное удаление по шаблону для разных backends"""
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(pattern)
    else:
        cache.clear()


def invalidate_mail_cache(user):
    """
    Сбрасывает кэш списка сообщений.
    Если передан конкретный пользователь — удаляет кэш только для него.
    Если пользователь — модератор или суперпользователь — очищает все ключи сообщений.
    """
    user_types = ["anon", "owner", "moderator"]
    if user is not None and user.is_authenticated:
        if is_moderator:
            for user_type in user_types:
                pattern = f"mailings_user_{user_type}_*"
                safe_delete_pattern(pattern)
        else:
            cache_key = f"mailings_user_owner_{user.pk}"
            cache.delete(cache_key)
    else:
        for user_type in user_types:
            pattern = f"mailings_user_{user_type}_*"
            safe_delete_pattern(pattern)


def  check_user_can_create_mail(user):
    """Проверяет, имеет ли пользователь право создавать сообщения"""
    if is_moderator(user) and not user.is_superuser:
        raise PermissionDenied("Модераторам запрещено создавать сообщения")


def check_user_can_edit_mail(user, mail):
    """Проверяет, имеет ли пользователь право редактировать сообщение"""
    if user.is_superuser or mail.owner == user:
        return
    raise PermissionDenied("Вы не можете редактировать чужое сообщение")


def check_user_can_delete_mail(user, mail):
    """Проверяет, имеет ли пользователь право удалить сообщение"""
    if user.is_superuser or mail.owner == user:
        return
    raise PermissionDenied("Вы не можете удалить чужое сообщение")


def search_mailings(query: str, cache_timeout: int = CACHE_TIMEOUT) -> QuerySet:
    """
    Возвращает QuerySet сообщений, соответствующих поисковому запросу.
    Разбивает строку на слова и ищет их в subject
    """
    if not query:
        return Mailing.objects.none()

    cache_key = f"search_mailings:{query.lower()}"
    cached_ids = cache.get(cache_key)
    if cached_ids is not None:
        return Mailing.objects.filter(id__in=cached_ids)

    keywords = re.findall(r'\w+', query)
    q_objects = Q()
    for word in keywords:
        q_objects &= Q(subject__icontains=word)

    queryset = Mailing.objects.filter(q_objects)

    ids = list(queryset.values_list("id", flat=True))
    cache.set(cache_key, ids, cache_timeout)

    return queryset
