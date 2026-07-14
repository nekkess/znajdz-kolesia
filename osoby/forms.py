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
    source (title + URL) and the person's one party membership on top of
    the plain Person fields - handled in the view since they aren't
    Person fields. Editing assumes a single membership per person,
    matching the single-source convention already used here; people
    with several historical memberships still need Django admin."""

    source_title = forms.CharField(
        label="Nazwa źródła",
        required=False
    )

    source_url = forms.URLField(
        label="Link do źródła",
        required=False
    )

    membership_party = forms.CharField(
        label="Partia (przynależność)",
        required=False
    )

    membership_start_year = forms.IntegerField(
        label="Rok rozpoczęcia (partia)",
        required=False
    )

    membership_end_year = forms.IntegerField(
        label="Rok zakończenia (partia, puste = nadal)",
        required=False
    )

    membership_position = forms.CharField(
        label="Funkcja w partii",
        required=False
    )

    membership_family_relation = forms.CharField(
        label="Powiązanie rodzinne (zamiast funkcji)",
        required=False
    )

    membership_description = forms.CharField(
        label="Opis przynależności partyjnej",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = Person

        fields = PERSON_FIELDS

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

        labels = PERSON_LABELS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            membership = self.instance.memberships.first()

            if membership:
                self.fields["membership_party"].initial = membership.party.name
                self.fields["membership_start_year"].initial = membership.start_year
                self.fields["membership_end_year"].initial = membership.end_year
                self.fields["membership_position"].initial = membership.position
                self.fields["membership_family_relation"].initial = membership.family_relation
                self.fields["membership_description"].initial = membership.description


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
