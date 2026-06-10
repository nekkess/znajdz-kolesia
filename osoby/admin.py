from django.contrib import admin
from .models import PersonSource

from .models import (
    Person,
    Party,
    PartyMembership,
    PersonSource
)


class PersonSourceInline(admin.TabularInline):
    model = PersonSource
    extra = 1


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    inlines = [PersonSourceInline]


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    pass


@admin.register(PartyMembership)
class PartyMembershipAdmin(admin.ModelAdmin):
    pass