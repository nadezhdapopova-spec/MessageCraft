import logging
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from faker import Faker

from campaigns.models import Attempt, Campaign
from clients.models import Client
from mailings.models import Mailing
from users.models import CustomUser

logger = logging.getLogger("users")


fake = Faker("ru_RU")

MAIL_THEMES = [
    "Новости компании",
    "Акции и скидки",
    "Советы и рекомендации",
    "Оповещения о событиях",
    "Информационный бюллетень",
]


class Command(BaseCommand):
    help = "Генерация тестовых данных: пользователи, клиенты, рассылки, кампании, попытки отправки"

    def handle(self, *args, **options):
        logger.info("Запущена генерация тестовых данных")
        self.stdout.write("Начинаем генерацию тестовых данных...")
        try:
            users = []
            for i in range(10):
                user = CustomUser.objects.create_user(
                    username=f"user{i+1}",
                    email=f"user{i+1}@example.com",
                    password="password123",
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone_number=fake.phone_number(),
                    country="RU",
                )
                users.append(user)

            for user in users:
                clients = []
                for _ in range(random.randint(5, 10)):
                    client = Client.objects.create(
                        email=fake.unique.email(), full_name=fake.name(), comment=fake.sentence(), owner=user
                    )
                    clients.append(client)

                mailings = []
                for _ in range(random.randint(1, 5)):
                    theme = random.choice(MAIL_THEMES)
                    subject = f"{theme}: {fake.sentence(nb_words=4)}"
                    body = (
                        f"<h1>{theme}</h1>"
                        f"<p>{fake.paragraph(nb_sentences=3)}</p>"
                        f"<p>Благодарим за внимание!</p>"
                    )
                    mailing = Mailing.objects.create(subject=subject, body=body, is_html=True, owner=user)
                    mailings.append(mailing)

                for mailing in mailings:
                    campaign = Campaign.objects.create(
                        name=f"{mailing.subject} Campaign",
                        message=mailing,
                        start_at=timezone.now(),
                        end_at=timezone.now() + timezone.timedelta(days=random.randint(1, 5)),
                        status=random.choice(["CREATED", "RUNNING", "FINISHED"]),
                        owner=user,
                    )

                    selected_clients = random.sample(clients, k=random.randint(1, len(clients)))
                    campaign.recipients.set(selected_clients)

                    for client in selected_clients:
                        for _ in range(random.randint(1, 3)):
                            Attempt.objects.create(
                                campaign=campaign,
                                recipient=client,
                                status=random.choice(["SUCCESS", "FAIL"]),
                                response=fake.sentence(),
                                timestamp=timezone.now() - timezone.timedelta(minutes=random.randint(0, 1000)),
                            )

            self.stdout.write(self.style.SUCCESS("Тестовые данные с тематикой и HTML письмами успешно сгенерированы!"))
        except Exception as e:
            logger.error(f"Ошибка генерации данных: {e}")
            self.stderr.write(self.style.ERROR(f"Ошибка генерации данных: {e}"))
