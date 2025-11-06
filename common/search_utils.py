import re
from django.db.models import Q, Model
from django.core.cache import cache
from .cache_utils import CACHE_TIMEOUT


def search_objects(query: str, model: type[Model], cache_timeout: int = CACHE_TIMEOUT):
    """Поиск клиентов по email, ФИО и комментарию"""
    app_name = model._meta.app_label

    if not query:
        return model.objects.none()

    cache_key = f"search_{app_name}:{query.lower()}"
    cached_ids = cache.get(cache_key)
    if cached_ids is not None:
        return model.objects.filter(id__in=cached_ids)

    keywords = re.findall(r'\w+', query)
    q_objects = Q()
    for word in keywords:
        q_objects &= (
            Q(email__icontains=word) |
            Q(full_name__icontains=word) |
            Q(comment__icontains=word)
        )

    queryset = model.objects.filter(q_objects)
    ids = list(queryset.values_list("id", flat=True))
    cache.set(cache_key, ids, cache_timeout)

    return queryset
