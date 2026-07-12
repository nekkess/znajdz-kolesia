from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
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

        creating = not self.pk

        super().save(*args, **kwargs)

        # geocode tylko dla nowych i tylko jeśli city istnieje
        if creating and self.city:

            try:
                geolocator = Nominatim(user_agent="zlodziejpl")

                location = geolocator.geocode(
                    f"{self.city}, Polska",
                    timeout=10
                )

                if location:
                    Person.objects.filter(pk=self.pk).update(
                        latitude=location.latitude,
                        longitude=location.longitude
                    )

            except Exception:
                pass

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
    def share_summary(self):
        text = f"{self.first_name} {self.last_name}"

        role_bits = [bit for bit in (self.position, self.organization) if bit]
        if role_bits:
            text += " - " + ", ".join(role_bits)

        if self.salary_display != "Brak danych":
            text += f" 💰 {self.salary_display}"

        return text

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

    family_relation = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Powiązanie rodzinne",
        help_text="Np. 'szwagierka', 'syn', 'żona'. Wypełnij zamiast "
                  "traktować osobę jako formalnego członka partii - "
                  "wyświetli się zamiast okresu przynależności."
    )

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


class PersonSubmission(models.Model):
    STATUS_CHOICES = [
        ("pending", "Oczekujące"),
        ("approved", "Zaakceptowane"),
        ("rejected", "Odrzucone"),
    ]

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions"
    )

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

    annual_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    party = models.CharField(max_length=200, blank=True)

    description = models.TextField(verbose_name="Opis powiązania")

    photo = CloudinaryField('image', blank=True, null=True)

    source_title = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(verbose_name="Link do źródła")

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_status_display()})"

    def approve(self):
        """Create the real Person (+ source) from this submission and
        mark it approved. No-op if it isn't pending."""

        if self.status != "pending":
            return None

        person = Person.objects.create(
            first_name=self.first_name,
            last_name=self.last_name,
            position=self.position,
            organization=self.organization,
            city=self.city,
            voivodeship=self.voivodeship,
            annual_salary=self.annual_salary,
            party=self.party,
            description=self.description,
            photo=self.photo,
        )

        if self.source_url:
            PersonSource.objects.create(
                person=person,
                title=self.source_title or self.source_url,
                url=self.source_url,
            )

        self.status = "approved"
        self.reviewed_at = timezone.now()
        self.save()

        return person

    def reject(self):
        if self.status != "pending":
            return

        self.status = "rejected"
        self.reviewed_at = timezone.now()
        self.save()