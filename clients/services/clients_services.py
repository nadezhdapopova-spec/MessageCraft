import re

from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet, Q
from django.http import Http404

from clients.models import Client


CACHE_TIMEOUT = 60 * 15


def is_moderator(user):
    """Проверяет, состоит ли пользователь в группе модераторов"""
    return user.is_superuser or user.groups.filter(name="moderator").exists()


def get_visible_clients_for_user(user):
    """
    Если пользователь авторизован и владелец рассылки, возвращает список получателей его рассылки.
    Если пользователь - модератор, возвращает список всех получателей рассылки
    """
    if not user.is_authenticated:
        return Client.objects.none()
    if is_moderator(user):
        return Client.objects.select_related("owner").order_by("owner")
    return Client.objects.filter(owner=user)


def get_cached_clients(user, timeout=CACHE_TIMEOUT):
    """Возвращает кэшированный список получателей рассылки с учётом прав пользователя"""
    user_type = (
        "moderator" if is_moderator(user)
        else "owner" if user.is_authenticated
        else "anon"
    )
    cache_key = f"clients_user_{user_type}_{user.pk if user.is_authenticated else 'anon'}"
    queryset = cache.get(cache_key)
    if queryset is not None:
        return queryset

    queryset = get_visible_clients_for_user(user)
    queryset = queryset.select_related("owner")
    cache.set(cache_key, queryset, timeout)
    return queryset


def can_user_view_client(user, client):
    """
        Проверяет, имеет ли пользователь право просматривать карточку получателя рассылки.
        Возбуждается Http404: 'Информация недоступна', если доступ запрещён
        """
    if not user.is_authenticated:
        raise Http404("Информация недоступна")
    else:
        if not is_moderator and client.owner != user:
            raise Http404("Информация недоступна")


def safe_delete_pattern(pattern):
    """Безопасное удаление по шаблону для разных backends"""
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(pattern)
    else:
        cache.clear()


def invalidate_client_cache(user):
    """
    Сбрасывает кэш списка клиентов.
    Если передан конкретный пользователь — удаляет кэш только для него.
    Если пользователь — модератор или суперпользователь — очищает все ключи клиентов.
    """
    user_types = ["anon", "owner", "moderator"]
    if user is not None and user.is_authenticated:
        if is_moderator:
            for user_type in user_types:
                pattern = f"clients_user_{user_type}_*"
                safe_delete_pattern(pattern)
        else:
            cache_key = f"clients_user_owner_{user.pk}"
            cache.delete(cache_key)
    else:
        for user_type in user_types:
            pattern = f"clients_user_{user_type}_*"
            safe_delete_pattern(pattern)


def  check_user_can_create_client(user):
    """Проверяет, имеет ли пользователь право создавать карточку получателя рассылки"""
    if is_moderator(user) and not user.is_superuser:
        raise PermissionDenied("Модераторам запрещено создавать карточки получателей рассылки")


def check_user_can_edit_client(user, client):
    """Проверяет, имеет ли пользователь право редактировать товар"""
    if user.is_superuser or client.owner == user:
        return
    raise PermissionDenied("Вы не можете редактировать чужую карточку получателя рассылки")


def check_user_can_delete_client(user, client):
    """Проверяет, имеет ли пользователь право удалить карточку получателя рассылки"""
    if user.is_superuser or client.owner == user:
        return
    raise PermissionDenied("Вы не можете удалить чужую карточку получателя рассылки")


def search_clients(query: str, cache_timeout: int = CACHE_TIMEOUT) -> QuerySet:
    """
    Возвращает QuerySet товаров, соответствующих поисковому запросу.
    Разбивает строку на слова и ищет их в name, brief_description и description.
    """
    if not query:
        return Client.objects.none()

    cache_key = f"search_clients:{query.lower()}"
    cached_ids = cache.get(cache_key)
    if cached_ids is not None:
        return Client.objects.filter(id__in=cached_ids)

    keywords = re.findall(r'\w+', query)
    q_objects = Q()
    for word in keywords:
        q_objects &= (Q(email__icontains=word) |
                      Q(full_name__icontains=word) |
                      Q(comment__icontains=word))

    queryset = Client.objects.filter(q_objects)

    ids = list(queryset.values_list("id", flat=True))
    cache.set(cache_key, ids, cache_timeout)

    return queryset
