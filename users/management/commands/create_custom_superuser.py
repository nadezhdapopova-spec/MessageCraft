import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError

logger = logging.getLogger("users")


class Command(BaseCommand):
    help = "Создает суперпользователя, если он не создан"

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            if not User.objects.filter(email="admin@sky.pro").exists():
                User.objects.create_superuser(
                    email="admin@sky.pro",
                    password="123qwe456rty",
                    first_name="Admin",
                    last_name="Admin",
                    username="Admin",
                )
                logger.info("Суперпользователь успешно создан")
                self.stdout.write(self.style.SUCCESS("Суперпользователь admin@sky.pro успешно создан"))
            else:
                logger.warning("Суперпользователь уже существует")
                self.stdout.write(self.style.WARNING("Суперпользователь admin@sky.pro уже существует"))
        except IntegrityError as e:
            logger.error(f"Ошибка создания суперпользователя: {e}")
            self.stdout.write(self.style.ERROR(f"Ошибка создания суперпользователя: {e}"))
