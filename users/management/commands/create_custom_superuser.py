from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError


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
                    username="Admin"
                )
                self.stdout.write(self.style.SUCCESS("Superuser admin@sky.pro успешно создан"))
            else:
                self.stdout.write(self.style.WARNING("Superuser admin@sky.pro уже существует"))
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f"Ошибка создания суперпользователя: {e}"))
