import logging

from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from campaigns.models import Attempt, Campaign
from config import settings

logger = logging.getLogger("campaigns")


def send_campaign(campaign: Campaign) -> None:
    """
    Отправляет рассылку всем получателям и создаёт записи Attempt.
    Письма отправляются от DEFAULT_FROM_EMAIL,
    а ответы — на почту автора сообщения (через Reply-To)
    """
    logger.info(f"Запуск рассылки {campaign.id}: '{campaign.name}'")
    message = campaign.message
    from_email = settings.DEFAULT_FROM_EMAIL
    reply_to = [message.owner.email] if message.owner and message.owner.email else []

    total = campaign.recipients.count()
    success_count = 0
    fail_count = 0

    for client in campaign.recipients.all():
        try:
            email = EmailMultiAlternatives(
                subject=message.subject,
                body=message.body if not message.is_html else "",
                from_email=from_email,
                to=[client.email],
                reply_to=reply_to,
            )
            if message.is_html:
                email.attach_alternative(message.body, "text/html")
            email.send()

            Attempt.objects.create(campaign=campaign, recipient=client, status="SUCCESS", response="OK")
            success_count += 1
            logger.debug(f"Письмо отправлено {client.email}")

        except Exception as e:
            Attempt.objects.create(campaign=campaign, recipient=client, status="FAIL", response=str(e))
            fail_count += 1
            logger.error(f"Ошибка при отправке на {client.email}: {e}", exc_info=True)

    campaign.status = "RUNNING"
    campaign.save()
    logger.info(
        f"Рассылка {campaign.id} завершена: " f"успешно - {success_count}, ошибок - {fail_count}, всего - {total}"
    )


def send_scheduled_campaigns() -> None:
    """
    Отправка всех рассылок, которые должны быть отправлены сейчас:
    для автоматической отправки по расписанию
    """
    now = timezone.now()
    campaigns = Campaign.objects.filter(status="CREATED", start_at__lte=now)
    total = campaigns.count()

    if not total:
        logger.info("Нет рассылок для запуска")
        return

    logger.info(f"Найдено {total} рассылок для запуска ({now:%Y-%m-%d %H:%M:%S})")
    for campaign in campaigns:
        try:
            send_campaign(campaign)
        except Exception as e:
            logger.error(f"Ошибка при запуске рассылки {campaign.id}: {e}")


def check_user_can_send_campaign(user, campaign):
    """Проверяет, имеет ли пользователь право запустить рассылку"""
    if user.is_superuser or campaign.owner == user:
        return
    raise PermissionDenied("Вы не можете запустить чужую рассылку")


def disable_campaign(request_user, campaign):
    """Отключает рассылку, если у пользователя есть разрешение"""
    if not (request_user.is_superuser or request_user.has_perm("campaigns.can_disable_campaigns")):
        logger.warning("Попытка отключения рассылки пользователем без прав")
        raise PermissionDenied("У вас нет прав для отключения рассылок")

    campaign.status = "DISABLED"
    campaign.is_active = False
    campaign.save()
    logger.info(f"Рассылка {campaign.id} отключена")
