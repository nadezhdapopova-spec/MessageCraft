from django.core.management.base import BaseCommand

from campaigns.services.campaigns_services import send_scheduled_campaigns


class Command(BaseCommand):
    help = "Отправка запланированных рассылок"

    def handle(self, *args, **options):
        send_scheduled_campaigns()
        self.stdout.write(self.style.SUCCESS("Все запланированные рассылки отправлены"))
