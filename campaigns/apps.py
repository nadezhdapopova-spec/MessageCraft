import os

from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig

from campaigns.services.campaigns_services import send_scheduled_campaigns


class CampaignsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "campaigns"


    def ready(self):
        """Запускает планировщик при старте Django. Проверяет рассылки каждую минуту"""
        if os.environ.get("RUN_MAIN") != "true":
            return

        scheduler = BackgroundScheduler(timezone="Europe/Moscow")
        scheduler.add_job(send_scheduled_campaigns, "interval", minutes=1)
        scheduler.start()
