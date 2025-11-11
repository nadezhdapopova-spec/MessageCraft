import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from campaigns.models import Attempt, Campaign
from config import settings

logger = logging.getLogger("campaigns")
scheduler: BackgroundScheduler | None = None


def send_campaign(campaign_id: int) -> None:
    """
    Отправляет рассылку всем получателям и создаёт записи Attempt.
    Письма отправляются от DEFAULT_FROM_EMAIL,
    а ответы — на почту автора сообщения (через Reply-To)
    """
    try:
        campaign = Campaign.objects.get(pk=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"Рассылка {campaign_id} не найдена.")
        return
    if not campaign.is_active or campaign.status == "DISABLED":
        logger.info(f"Рассылка {campaign.id} ('{campaign.name}') отключена — запуск отменён.")
        return
    Campaign.objects.filter(pk=campaign.id).update(status="RUNNING")
    logger.info(f"Рассылка {campaign.id}: статус изменён на RUNNING")
    message = campaign.message
    from_email = settings.DEFAULT_FROM_EMAIL
    reply_to = [message.owner.email] if message.owner and message.owner.email else []

    total = campaign.recipients.count()
    success_count = 0
    fail_count = 0

    for client in campaign.recipients.all():
        campaign.refresh_from_db(fields=["is_active", "status"])
        if not campaign.is_active or campaign.status == "DISABLED":
            logger.info(f"Рассылка {campaign.id} была отключена во время отправки — процесс остановлен.")
            break
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

    campaign.refresh_from_db(fields=["is_active", "status"])
    if campaign.is_active and campaign.status != "DISABLED":
        Campaign.objects.filter(pk=campaign.pk).update(status="FINISHED")
        logger.info(
            f"Рассылка {campaign.id} завершена: успешно - {success_count}, ошибок - {fail_count}, всего - {total}"
        )


def send_scheduled_campaigns() -> None:
    """
    Отправка всех рассылок, которые должны быть отправлены сейчас:
    для автоматической отправки по расписанию
    """
    now = timezone.now()
    campaigns = Campaign.objects.filter(status="CREATED", is_active=True, start_at__lte=now)
    total = campaigns.count()

    if not total:
        logger.info("Нет рассылок для запуска")
        return

    for campaign in campaigns:
        try:
            Campaign.objects.filter(pk=campaign.pk).update(status="QUEUED")
            trigger = DateTrigger(run_date=now)
            scheduler.add_job(send_campaign, trigger, args=[campaign.pk])
            logger.info(f"Поставлена в очередь рассылка {campaign.id}: '{campaign.name}'")
        except Exception as e:
            logger.error(f"Ошибка при запуске рассылки {campaign.id}: {e}")
    logger.info(f"В очередь добавлено рассылок: {total}")


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

    global scheduler
    if scheduler:
        job_id = f"campaign_{campaign.id}"
        job = scheduler.get_job(job_id)
        if job:
            scheduler.remove_job(job_id)
            logger.info(f"Задача {job_id} удалена из планировщика (рассылка {campaign.id})")
        else:
            logger.debug(f"Для рассылки {campaign.id} не найдено активное задание в планировщике")


def enable_campaign(request_user, campaign):
    """Включает рассылку снова, если у пользователя есть разрешение"""
    if not (request_user.is_superuser or request_user.has_perm("campaigns.can_disable_campaigns")):
        logger.warning("Попытка включения рассылки пользователем без прав")
        raise PermissionDenied("У вас нет прав для включения рассылок")

    if campaign.status != "DISABLED":
        logger.warning(f"Рассылка {campaign.id} не отключена, включение невозможно")
        raise ValueError("Можно включить только отключённую рассылку")

    campaign.status = "CREATED"
    campaign.is_active = True
    campaign.save(update_fields=["status", "is_active"])
    logger.info(f"Рассылка {campaign.id} снова включена (статус: CREATED)")
