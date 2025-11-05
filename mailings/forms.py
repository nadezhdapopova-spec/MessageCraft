from django import forms
from .models import Mailing


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["subject", "body", "is_html"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 20}),
            "is_html": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
