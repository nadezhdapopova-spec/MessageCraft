import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import IntegrityError

logger = logging.getLogger("users")


class Command(BaseCommand):
    help = "Создает модератора товаров, если он не создан"

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            if not User.objects.filter(email="manager1@sky.pro").exists():
                user = User.objects.create_user(
                    email="manager1@sky.pro",
                    password="234qwe567rty",
                    first_name="Manager1",
                    last_name="Manager1",
                    username="manager1",
                    country="RU",
                    is_staff=True,
                )

                group, _ = Group.objects.get_or_create(name="manager")
                user.groups.add(group)
                logger.info(f"Пользователь {user.email} успешно создан")
                self.stdout.write(self.style.SUCCESS(f"Пользователь {user.email} успешно создан"))

            else:
                logger.warning("Пользователь уже существует")
                self.stdout.write(self.style.WARNING("Пользователь уже существует"))
        except IntegrityError as e:
            logger.error(f"Ошибка создания менеджера1: {e}")
            self.stderr.write(self.style.ERROR(f"Ошибка создания менеджера1: {e}"))
        except Exception as e:
            logger.error(f"Ошибка при создании менеджера1: {e}")
            self.stderr.write(self.style.ERROR(f"Неожиданная ошибка: {e}"))
