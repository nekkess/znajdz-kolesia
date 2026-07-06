from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import Person, PersonSubmission


class BootstrapFormMixin:
    """Adds Bootstrap form-control/form-select classes to every field
    automatically, so templates can render fields individually without
    repeating widget attrs everywhere."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = "form-select"
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
            else:
                widget.attrs["class"] = "form-control"
                # Bootstrap floating labels need a placeholder attribute
                # present (even empty) to detect an empty input.
                widget.attrs.setdefault("placeholder", " ")


PERSON_FIELDS = (
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
)

PERSON_LABELS = {
    "first_name": "Imię",
    "last_name": "Nazwisko",
    "position": "Stanowisko",
    "organization": "Organizacja",
    "city": "Miasto",
    "voivodeship": "Województwo",
    "annual_salary": "Roczne wynagrodzenie (jeśli znane)",
    "party": "Partia",
    "photo": "Zdjęcie (opcjonalnie)",
}


class PersonSubmissionForm(BootstrapFormMixin, forms.ModelForm):

    class Meta:
        model = PersonSubmission

        fields = PERSON_FIELDS + ("source_title", "source_url")

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

        labels = {
            **PERSON_LABELS,
            "source_title": "Nazwa źródła",
            "source_url": "Link do źródła",
        }


class PersonForm(BootstrapFormMixin, forms.ModelForm):
    """Used by the superuser-only add/edit pages. Adds a single optional
    source (title + URL) on top of the plain Person fields - handled in
    the view since it isn't a Person field."""

    source_title = forms.CharField(
        label="Nazwa źródła",
        required=False
    )

    source_url = forms.URLField(
        label="Link do źródła",
        required=False
    )

    class Meta:
        model = Person

        fields = PERSON_FIELDS

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

        labels = PERSON_LABELS


class LoginForm(BootstrapFormMixin, AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nazwa użytkownika"
        self.fields["password"].label = "Hasło"


class RegisterForm(BootstrapFormMixin, UserCreationForm):

    email = forms.EmailField(required=True, label="Adres e-mail")

    class Meta:
        model = User

        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nazwa użytkownika"
        self.fields["password1"].label = "Hasło"
        self.fields["password2"].label = "Powtórz hasło"
        for field in ("username", "password1", "password2"):
            self.fields[field].help_text = None
