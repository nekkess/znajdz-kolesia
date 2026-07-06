from django.contrib import admin

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
            submission.approve()
            approved += 1

        self.message_user(request, f"Zaakceptowano {approved} zgloszen.")

    approve_submissions.short_description = "Zatwierdz wybrane zgloszenia"

    def reject_submissions(self, request, queryset):
        rejected = 0

        for submission in queryset.filter(status="pending"):
            submission.reject()
            rejected += 1

        self.message_user(request, f"Odrzucono {rejected} zgloszen.")

    reject_submissions.short_description = "Odrzuc wybrane zgloszenia"