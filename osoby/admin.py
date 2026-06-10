from django.contrib import admin
from .models import Person, Party, PartyMembership, PersonSource


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

    def save_model(self, request, obj, form, change):
        # 🔥 KLUCZ: zapisz PERSON bez inline
        obj.save()

    def save_related(self, request, form, formsets, change):
        # 🔥 KLUCZ: dopiero potem inline
        super().save_related(request, form, formsets, change)


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    pass


@admin.register(PartyMembership)
class PartyMembershipAdmin(admin.ModelAdmin):
    pass