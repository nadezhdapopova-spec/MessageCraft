import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand

from reports.models import Contacts

logger = logging.getLogger("reports")


class Command(BaseCommand):
    help = "Добавление контактной информации в базу данных из фикстуры"

    def handle(self, *args, **kwargs):
        try:
            Contacts.objects.all().delete()
            logger.info("Контактные данные удалены из базы данных")

            call_command("loaddata", "reports/fixtures/contacts_fixture.json")
            logger.info("Загружены контакты из фикструры")
            self.stdout.write(self.style.SUCCESS("Загружены контакты из фикструры"))

        except Exception as e:
            logger.error(f"Ошибка перезаписи данных: {e}")
            self.stderr.write(self.style.ERROR(f"Ошибка перезаписи данных: {e}"))
