from django.contrib.auth.models import AbstractUser
from django.db import models
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField


class CustomUser(AbstractUser):
    """Класс модели пользователя"""
    email = models.EmailField(unique=True, verbose_name="Email")
    first_name = models.CharField(max_length=100, blank=True, null=True, help_text="Необязательное поле")
    last_name = models.CharField(max_length=100, blank=True, null=True, help_text="Необязательное поле")
    phone_number = PhoneNumberField(region='RU', blank=True, null=True, verbose_name="Номер телефона", help_text="Необязательное поле")
    avatar = models.ImageField(upload_to="users/avatars/", blank=True, null=True, verbose_name="Аватар", default="users/images/default.png")
    country = CountryField(blank_label="Выберите страну", default="RU", verbose_name="Страна")
    is_blocked = models.BooleanField(default=False, verbose_name="заблокирован")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username",]


    def __str__(self):
        return self.email


    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"
        ordering = ["email",]
