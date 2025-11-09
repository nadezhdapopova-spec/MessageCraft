import logging
import os

from django.apps import AppConfig

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger("campaigns")


class CampaignsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "campaigns"

    def ready(self):
        """Запускает планировщик при старте Django. Проверяет рассылки каждую минуту"""
        if os.environ.get("RUN_MAIN") != "true":
            logger.debug("Пропуск запуска планировщика (RUN_MAIN != true)")
            return

        from campaigns.services.campaigns_services import send_scheduled_campaigns

        scheduler = BackgroundScheduler(timezone="Europe/Moscow")
        scheduler.add_job(send_scheduled_campaigns, "interval", minutes=1)
        scheduler.start()

        logger.info("Планировщик рассылок успешно запущен (интервал: 1 минута)")
