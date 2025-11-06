from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail

from campaigns.models import Campaign, Attempt
from config import settings


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


def check_user_can_send_campaign(user, campaign):
    """Проверяет, имеет ли пользователь право запустить рассылку"""
    if user.is_superuser or campaign.owner == user:
        return
    raise PermissionDenied("Вы не можете запустить чужую рассылку")
