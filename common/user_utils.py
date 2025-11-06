from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model

from campaigns.models import Campaign
from .permissions import is_manager
from .cache_utils import cache, CACHE_TIMEOUT, safe_delete_pattern


def get_visible_objects_for_user(user, model: type[Model]):
    """Возвращает список клиентов, доступных пользователю"""
    if not hasattr(model, "owner"):
        raise ImproperlyConfigured(f"Модель {model.__name__} не имеет поля 'owner'")

    if not user.is_authenticated:
        return model.objects.none()
    if is_manager(user):
        return model.objects.select_related("owner").order_by("owner")
    return model.objects.filter(owner=user)


def get_cached_objects(user, model: type[Model], timeout=CACHE_TIMEOUT):
    """Возвращает кэшированный список клиентов"""
    app_name = model._meta.app_label

    user_type = (
        "manager" if is_manager(user)
        else "owner" if user.is_authenticated
        else "anon"
    )
    cache_key = f"{app_name}_user_{user_type}_{user.pk if user.is_authenticated else 'anon'}"
    queryset = cache.get(cache_key)
    if queryset is not None:
        return queryset

    queryset = get_visible_objects_for_user(user, model).select_related("owner")
    if model == Campaign:
        queryset.order_by("-created_at")
    cache.set(cache_key, queryset, timeout)
    return queryset


def invalidate_obj_cache(user, app_name):
    """Сбрасывает кэш клиентов"""
    user_types = ["anon", "owner", "manager"]
    if user and user.is_authenticated:
        if is_manager(user):
            for t in user_types:
                safe_delete_pattern(f"{app_name}_user_{t}_*")
        else:
            cache.delete(f"{app_name}_user_owner_{user.pk}")
    else:
        for t in user_types:
            safe_delete_pattern(f"{app_name}_user_{t}_*")
