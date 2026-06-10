from django.db import models
from django.contrib.auth.models import User
from geopy.geocoders import Nominatim
from cloudinary.models import CloudinaryField

VOIVODESHIPS = [
    ("dolnoslaskie", "Dolnośląskie"),
    ("kujawsko_pomorskie", "Kujawsko-Pomorskie"),
    ("lubelskie", "Lubelskie"),
    ("lubuskie", "Lubuskie"),
    ("lodzkie", "Łódzkie"),
    ("malopolskie", "Małopolskie"),
    ("mazowieckie", "Mazowieckie"),
    ("opolskie", "Opolskie"),
    ("podkarpackie", "Podkarpackie"),
    ("podlaskie", "Podlaskie"),
    ("pomorskie", "Pomorskie"),
    ("slaskie", "Śląskie"),
    ("swietokrzyskie", "Świętokrzyskie"),
    ("warminsko_mazurskie", "Warmińsko-Mazurskie"),
    ("wielkopolskie", "Wielkopolskie"),
    ("zachodniopomorskie", "Zachodniopomorskie"),
]


class Person(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    position = models.CharField(max_length=255, blank=True)

    organization = models.CharField(max_length=255, blank=True)

    city = models.CharField(max_length=100, blank=True)

    voivodeship = models.CharField(
        max_length=50,
        choices=VOIVODESHIPS,
        blank=True
    )

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    annual_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    photo = CloudinaryField('image', blank=True, null=True)


    description = models.TextField(
        blank=True,
        verbose_name="Opis działalności"
    )

    party = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Partia"
    )

    def save(self, *args, **kwargs):

        if self.city:

            try:
                geolocator = Nominatim(user_agent="zlodziejpl")

                location = geolocator.geocode(
                    f"{self.city}, Polska",
                    addressdetails=True,
                    timeout=10
                )

                if location:
                    self.latitude = location.latitude
                    self.longitude = location.longitude

                    address = location.raw.get("address", {})
                    state = address.get("state", "")

                    mapping = {
                        "Województwo dolnośląskie": "dolnoslaskie",
                        "Województwo kujawsko-pomorskie": "kujawsko_pomorskie",
                        "Województwo lubelskie": "lubelskie",
                        "Województwo lubuskie": "lubuskie",
                        "Województwo łódzkie": "lodzkie",
                        "Województwo małopolskie": "malopolskie",
                        "Województwo mazowieckie": "mazowieckie",
                        "Województwo opolskie": "opolskie",
                        "Województwo podkarpackie": "podkarpackie",
                        "Województwo podlaskie": "podlaskie",
                        "Województwo pomorskie": "pomorskie",
                        "Województwo śląskie": "slaskie",
                        "Województwo świętokrzyskie": "swietokrzyskie",
                        "Województwo warmińsko-mazurskie": "warminsko_mazurskie",
                        "Województwo wielkopolskie": "wielkopolskie",
                        "Województwo zachodniopomorskie": "zachodniopomorskie",
                    }

                    if state in mapping:
                        self.voivodeship = mapping[state]

            except Exception:
                pass

        super().save(*args, **kwargs)

    @property
    def salary_display(self):
        if self.annual_salary:
            return f"{int(self.annual_salary):,} zł"

        if self.salary_min and self.salary_max:
            return (
                f"{int(self.salary_min):,} - "
                f"{int(self.salary_max):,} zł"
            )

        return "Brak danych"

    @property
    def current_party(self):
        membership = self.memberships.last()
        return membership.party.name if membership else ""

    @property
    def upvotes(self):
        return self.votes.filter(vote=1).count()

    @property
    def downvotes(self):
        return self.votes.filter(vote=-1).count()

    @property
    def approval_percent(self):
        total = self.upvotes + self.downvotes

        if total == 0:
            return 0

        return round(self.upvotes * 100 / total)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Party(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PersonSource(models.Model):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="sources"
    )

    title = models.CharField(max_length=255)
    url = models.URLField()

    def __str__(self):
        return self.title


class PartyMembership(models.Model):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    party = models.ForeignKey(Party, on_delete=models.CASCADE)

    start_year = models.IntegerField()

    end_year = models.IntegerField(null=True, blank=True)

    position = models.CharField(max_length=255, blank=True)

    description = models.TextField(blank=True)

    class Meta:
        ordering = ["start_year"]
        constraints = [
            models.UniqueConstraint(
                fields=["person", "party", "start_year", "end_year"],
                name="unique_party_membership"
            )
        ]

    def __str__(self):
        return f"{self.person} - {self.party}"


class PersonVote(models.Model):
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="votes"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    vote = models.IntegerField(choices=[(1, "Upvote"), (-1, "Downvote")])

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("person", "user")