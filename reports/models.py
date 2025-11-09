from django.db import models


class Contacts(models.Model):
    """Класс контактной информации"""

    country = models.CharField(max_length=20, verbose_name="Страна")
    address = models.CharField(max_length=150, verbose_name="Юридический адрес")
    email = models.EmailField(max_length=50, verbose_name="Адрес электронной почты")

    def __str__(self):
        return f"{self.country} {self.address} {self.email}"

    class Meta:
        verbose_name = "контакты"
        verbose_name_plural = "контакты"
        ordering = [
            "country",
            "address",
        ]


class MessageFeedback(models.Model):
    """Класс обратной связи пользователей"""

    name = models.CharField(max_length=150, verbose_name="Имя пользователя")
    email = models.EmailField(verbose_name="E-mail пользователя")
    message = models.TextField(max_length=2000, verbose_name="Сообщение пользователя")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"{self.name} {self.email} {self.message}"

    class Meta:
        verbose_name = "обратная связь"
        verbose_name_plural = "обратная связь"
        ordering = [
            "name",
            "email",
            "created_at",
        ]
