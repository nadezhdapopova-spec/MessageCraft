from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm

from .models import CustomUser


class CustomClearableFileInput(forms.ClearableFileInput):
    """Класс для создания кастомного поля формы для загрузки файлов"""
    template_name = "widgets/custom_file_input.html"


class CustomUserCreationForm(UserCreationForm):
    """Класс формы для регистрации пользователя"""
    username = forms.CharField(max_length=150, help_text="Не более 150 символов. Только буквы, цифры и символы @/./+/-/_.")


    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("email", "username", "first_name", "last_name", "country", "phone_number",
                  "avatar", "password1", "password2")
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
        if hasattr(avatar, "content_type"):
            if avatar.content_type not in ["avatar/jpeg", "avatar/png"]:
                raise forms.ValidationError("Файл должен быть в формате JPEG или PNG")
            max_size_mb = 5
            if avatar.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(f"Размер файла не должен превышать {max_size_mb} МБ")
        return avatar


class UserProfileForm(forms.ModelForm):
    """Форма для личных данных"""
    class Meta:
        model = CustomUser
        fields = [
            "email", "first_name", "last_name", "username",
            "country", "phone_number", "avatar", "password1", "password2"
        ]
        widgets = {
            "email": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.Select(attrs={"class": "form-select"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "+7 999 123 45 67"}),
            "avatar": CustomClearableFileInput(attrs={"class": "form-control"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control"}),
        }


class UserPasswordForm(PasswordChangeForm):
    """Форма смены пароля"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
