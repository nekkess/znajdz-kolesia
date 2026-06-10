from django.contrib import admin
from .models import (
    Person,
    Party,
    PartyMembership,
    PersonSource
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

    # 🔥 KLUCZOWA POPRAWKA
    def save_model(self, request, obj, form, change):
        obj.save()  # zapisuje Person PIERWSZY
        form.save_m2m()  # potem relacje many-to-many (bez crasha)


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    pass


@admin.register(PartyMembership)
class PartyMembershipAdmin(admin.ModelAdmin):
    pass