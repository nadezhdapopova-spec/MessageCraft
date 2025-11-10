from django import forms
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import CustomUser


class CustomClearableFileInput(forms.ClearableFileInput):
    """Класс для создания кастомного поля формы для загрузки файлов"""

    template_name = "users/widgets/custom_file_input.html"


class CustomUserCreationForm(UserCreationForm):
    """Класс формы для регистрации пользователя"""

    username = forms.CharField(
        max_length=150, help_text="Не более 150 символов. Только буквы, цифры и символы @/./+/-/_."
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "country",
            "phone_number",
            "avatar",
            "password1",
            "password2",
        )
        widgets = {
            "email": forms.TextInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.Select(attrs={"class": "form-select"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "+7 999 123 45 67"}),
            "avatar": CustomClearableFileInput(attrs={"class": "form-control"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def clean_avatar(self):
        """Метод валидации поля формы 'аватар' на формат и размер файла"""
        avatar = self.cleaned_data.get("avatar")
        if not avatar or isinstance(avatar, str):
            return avatar
        valid_content_types = ["image/jpeg", "image/png"]
        if avatar.content_type not in valid_content_types:
            raise forms.ValidationError("Файл должен быть в формате JPEG или PNG")
        valid_extensions = [".jpg", ".jpeg", ".png"]
        import os

        ext = os.path.splitext(avatar.name)[1].lower()
        if ext not in valid_extensions:
            raise forms.ValidationError("Недопустимое расширение файла. Используйте JPG или PNG")
        max_size_mb = 5
        if avatar.size > max_size_mb * 1024 * 1024:
            raise forms.ValidationError(f"Размер файла не должен превышать {max_size_mb} МБ")
        return avatar


class UserProfileForm(forms.ModelForm):
    """Форма для личных данных"""

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "username",
            "country",
            "phone_number",
            "avatar",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.Select(attrs={"class": "form-select"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "+7 999 123 45 67"}),
            "avatar": CustomClearableFileInput(attrs={"class": "form-control"}),
        }


class UserPasswordForm(PasswordChangeForm):
    """Форма для смены пароля"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


class CustomPasswordResetForm(PasswordResetForm):
    """Класс восстановления пароля пользователя"""

    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control"}))

    def clean_email(self):
        """Валидация указанного email пользователя"""
        email = self.cleaned_data.get("email")
        if not CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email не найден")
        return email

    def save(self, *args, **kwargs):
        """Использование кастомного письма для восстановления пароля пользователя"""
        if "html_email_template_name" not in kwargs or kwargs["html_email_template_name"] is None:
            kwargs["html_email_template_name"] = "users/password_reset_email.html"
        return super().save(*args, **kwargs)


class CustomSetPasswordForm(SetPasswordForm):
    """Класс для создания и сохранения нового пароля пользователя"""

    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))
