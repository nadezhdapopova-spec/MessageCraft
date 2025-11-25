import atexit
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

        import campaigns.services.campaigns_services as services

        scheduler_instance = BackgroundScheduler(timezone="Europe/Moscow")
        scheduler_instance.add_job(services.send_scheduled_campaigns, "interval", minutes=1)
        scheduler_instance.start()

        services.scheduler = scheduler_instance
        atexit.register(lambda: scheduler_instance.shutdown(wait=False))

        logger.info("Планировщик рассылок успешно запущен (интервал: 1 минута)")
