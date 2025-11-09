import logging

from django.core.management.base import BaseCommand

from campaigns.services.campaigns_services import send_scheduled_campaigns

logger = logging.getLogger("campaigns")


class Command(BaseCommand):
    help = "Отправка запланированных рассылок"

    def handle(self, *args, **options):
        try:
            send_scheduled_campaigns()
            logger.info("Все запланированные рассылки отправлены")
            self.stdout.write(self.style.SUCCESS("Все запланированные рассылки отправлены"))
        except Exception as e:
            logger.exception("Ошибка при отправке рассылок")
            self.stdout.write(self.style.ERROR(f"Ошибка при отправке рассылок: {e}"))
