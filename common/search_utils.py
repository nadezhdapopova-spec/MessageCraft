import re

from django.core.cache import cache
from django.db.models import Model, Q, QuerySet

from .cache_utils import CACHE_TIMEOUT


def search_objects(query: str, source, cache_timeout: int = CACHE_TIMEOUT):
    """Универсальный поиск с автоматическим выбором полей для моделей"""
    if not query:
        return source.none() if isinstance(source, QuerySet) else source.objects.none()

    if isinstance(source, QuerySet):
        model = source.model
        queryset = source
    elif issubclass(source, Model):
        model = source
        queryset = model.objects.all()
    else:
        raise TypeError(f"search_objects ожидает Model или QuerySet, а получено {type(source)}")

    app_name = model._meta.app_label
    cache_key = f"search_{app_name}:{query.lower()}"
    cached_ids = cache.get(cache_key)
    if cached_ids is not None:
        return queryset.filter(id__in=cached_ids)

    if model.__name__ == "Client":
        search_fields = ["email", "full_name", "comment"]
    elif model.__name__ == "Campaign":
        search_fields = ["name", "status", "message__subject", "message__body"]
    else:
        search_fields = [
            f.name
            for f in model._meta.get_fields()
            if hasattr(f, "attname") and f.get_internal_type() in ["CharField", "TextField"]
        ]

    keywords = re.findall(r"\w+", query)
    q_objects = Q()
    for word in keywords:
        sub_q = Q()
        for field in search_fields:
            sub_q |= Q(**{f"{field}__icontains": word})
        q_objects &= sub_q

    results = queryset.filter(q_objects).distinct()
    cache.set(cache_key, list(results.values_list("id", flat=True)), cache_timeout)

    return results
