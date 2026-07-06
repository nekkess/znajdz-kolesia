from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import PersonSubmission


class PersonSubmissionForm(forms.ModelForm):

    class Meta:
        model = PersonSubmission

        fields = (
            "first_name",
            "last_name",
            "position",
            "organization",
            "city",
            "voivodeship",
            "annual_salary",
            "party",
            "description",
            "photo",
            "source_title",
            "source_url",
        )

        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

        labels = {
            "first_name": "Imię",
            "last_name": "Nazwisko",
            "position": "Stanowisko",
            "organization": "Organizacja",
            "city": "Miasto",
            "voivodeship": "Województwo",
            "annual_salary": "Roczne wynagrodzenie (jeśli znane)",
            "party": "Partia",
            "photo": "Zdjęcie (opcjonalnie)",
            "source_title": "Nazwa źródła",
            "source_url": "Link do źródła",
        }


class RegisterForm(UserCreationForm):

    email = forms.EmailField(required=True)

    class Meta:
        model = User

        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )