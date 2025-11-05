import re

from datetime import datetime
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import QuerySet, Q
from django.http import Http404

from campaigns.models import Campaign, Attempt
from config import settings


CACHE_TIMEOUT = 60 * 15


def send_campaign(campaign: Campaign) -> None:
    """
    Отправляет рассылку всем получателям и создаёт записи Attempt.
    Письма отправляются от DEFAULT_FROM_EMAIL,
    а ответы — на почту автора сообщения (через Reply-To)
    """
    message = campaign.message
    from_email = settings.DEFAULT_FROM_EMAIL
    reply_to = message.owner.email if message.owner and message.owner.email else None

    common_kwargs = {
        "subject": message.subject,
        "message": message.body if not message.is_html else "",
        "html_message": message.body if message.is_html else None,
        "from_email": from_email,
    }
    if reply_to:
        common_kwargs["headers"] = {"Reply-To": reply_to}

    for client in campaign.recipients.all():
        try:
            send_mail(
                **common_kwargs,
                recipient_list=[client.email],
            )
            Attempt.objects.create(
                campaign=campaign,
                recipient=client,
                status="SUCCESS",
                response="OK"
            )
        except Exception as e:
            Attempt.objects.create(
                campaign=campaign,
                recipient=client,
                status="FAIL",
                response=str(e)
            )

    campaign.status = "RUNNING"
    campaign.save()


def send_scheduled_campaigns() -> None:
    """
    Отправка всех рассылок, которые должны быть отправлены сейчас:
    для автоматической отправки по расписанию
    """
    now = datetime.now()
    campaigns = Campaign.objects.filter(status="CREATED", start_at__lte=now)
    for campaign in campaigns:
        send_campaign(campaign)


def is_moderator(user):
    """Проверяет, состоит ли пользователь в группе модераторов"""
    return user.is_superuser or user.groups.filter(name="moderator").exists()


def get_visible_campaigns_for_user(user):
    """
    Если пользователь авторизован, возвращает список его рассылок.
    Если пользователь - модератор, возвращает список всех рассылок
    """
    if not user.is_authenticated:
        return Campaign.objects.none()
    if is_moderator(user):
        return Campaign.objects.select_related("message", "owner").order_by("-created_at")
    return Campaign.objects.filter(owner=user).order_by("-created_at")


def get_cached_campaigns(user, timeout=CACHE_TIMEOUT):
    """Возвращает кэшированный список рассылок с учётом прав пользователя"""
    user_type = (
        "moderator" if is_moderator(user)
        else "owner" if user.is_authenticated
        else "anon"
    )
    cache_key = f"campaigns_user_{user_type}_{user.pk if user.is_authenticated else 'anon'}"
    queryset = cache.get(cache_key)
    if queryset is not None:
        return queryset

    queryset = get_visible_campaigns_for_user(user)
    queryset = queryset.select_related("owner")
    cache.set(cache_key, queryset, timeout)
    return queryset


def can_user_view_campaign(user, campaign):
    """
        Проверяет, имеет ли пользователь право просматривать рассылку.
        Возбуждается Http404: 'Информация недоступна', если доступ запрещён
        """
    if not user.is_authenticated:
        raise Http404("Информация недоступна")
    else:
        if not is_moderator and campaign.owner != user:
            raise Http404("Информация недоступна")


def safe_delete_pattern(pattern):
    """Безопасное удаление по шаблону для разных backends"""
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(pattern)
    else:
        cache.clear()


def invalidate_campaign_cache(user):
    """
    Сбрасывает кэш списка рассылок.
    Если передан конкретный пользователь — удаляет кэш только для него.
    Если пользователь — модератор или суперпользователь — очищает все ключи рассылок.
    """
    user_types = ["anon", "owner", "moderator"]
    if user is not None and user.is_authenticated:
        if is_moderator:
            for user_type in user_types:
                pattern = f"campaigns_user_{user_type}_*"
                safe_delete_pattern(pattern)
        else:
            cache_key = f"campaigns_user_owner_{user.pk}"
            cache.delete(cache_key)
    else:
        for user_type in user_types:
            pattern = f"campaigns_user_{user_type}_*"
            safe_delete_pattern(pattern)


def  check_user_can_create_campaign(user):
    """Проверяет, имеет ли пользователь право создавать рассылки"""
    if is_moderator(user) and not user.is_superuser:
        raise PermissionDenied("Модераторам запрещено создавать рассылки")


def check_user_can_edit_campaign(user, campaign):
    """Проверяет, имеет ли пользователь право редактировать рассылки"""
    if user.is_superuser or campaign.owner == user:
        return
    raise PermissionDenied("Вы не можете редактировать чужую рассылку")


def check_user_can_delete_campaign(user, campaign):
    """Проверяет, имеет ли пользователь право удалить рассылку"""
    if user.is_superuser or campaign.owner == user:
        return
    raise PermissionDenied("Вы не можете удалить чужую рассылку")


def check_user_can_send_campaign(user, campaign):
    """Проверяет, имеет ли пользователь право запустить рассылку"""
    if user.is_superuser or campaign.owner == user:
        return
    raise PermissionDenied("Вы не можете запустить чужую рассылку")


def search_campaigns(query: str, cache_timeout: int = CACHE_TIMEOUT) -> QuerySet:
    """
    Возвращает QuerySet рассылок, соответствующих поисковому запросу.
    Разбивает строку на слова и ищет их в subject
    """
    if not query:
        return Campaign.objects.none()

    cache_key = f"search_campaigns:{query.lower()}"
    cached_ids = cache.get(cache_key)
    if cached_ids is not None:
        return Campaign.objects.filter(id__in=cached_ids)

    keywords = re.findall(r'\w+', query)
    q_objects = Q()
    for word in keywords:
        q_objects &= Q(name__icontains=word)

    queryset = Campaign.objects.filter(q_objects)

    ids = list(queryset.values_list("id", flat=True))
    cache.set(cache_key, ids, cache_timeout)

    return queryset
