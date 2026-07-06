from django.contrib import admin
from django.utils import timezone

from .models import (
    Person,
    Party,
    PartyMembership,
    PersonSource,
    PersonSubmission,
)


class PartyMembershipInline(admin.StackedInline):
    model = PartyMembership
    extra = 1


class PersonSourceInline(admin.TabularInline):
    model = PersonSource
    extra = 1


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):

    inlines = [
        PartyMembershipInline,
        PersonSourceInline
    ]


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    pass


@admin.register(PartyMembership)
class PartyMembershipAdmin(admin.ModelAdmin):
    pass


@admin.register(PersonSubmission)
class PersonSubmissionAdmin(admin.ModelAdmin):

    list_display = (
        "first_name",
        "last_name",
        "submitted_by",
        "status",
        "created_at",
    )

    list_filter = ("status",)
    actions = ["approve_submissions", "reject_submissions"]

    def approve_submissions(self, request, queryset):
        approved = 0

        for submission in queryset.filter(status="pending"):

            person = Person.objects.create(
                first_name=submission.first_name,
                last_name=submission.last_name,
                position=submission.position,
                organization=submission.organization,
                city=submission.city,
                voivodeship=submission.voivodeship,
                annual_salary=submission.annual_salary,
                party=submission.party,
                description=submission.description,
                photo=submission.photo,
            )

            if submission.source_url:
                PersonSource.objects.create(
                    person=person,
                    title=submission.source_title or submission.source_url,
                    url=submission.source_url,
                )

            submission.status = "approved"
            submission.reviewed_at = timezone.now()
            submission.save()
            approved += 1

        self.message_user(request, f"Zaakceptowano {approved} zgloszen.")

    approve_submissions.short_description = "Zatwierdz wybrane zgloszenia"

    def reject_submissions(self, request, queryset):
        updated = queryset.filter(status="pending").update(
            status="rejected",
            reviewed_at=timezone.now(),
        )

        self.message_user(request, f"Odrzucono {updated} zgloszen.")

    reject_submissions.short_description = "Odrzuc wybrane zgloszenia"