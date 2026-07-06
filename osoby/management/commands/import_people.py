import json

import cloudinary.uploader
from cloudinary import CloudinaryResource
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from osoby.models import Party, Person, PersonSource, PartyMembership


class Command(BaseCommand):
    help = "Bulk import/update Person records from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str)
        parser.add_argument(
            "--skip-photos",
            action="store_true",
            help="Don't fetch/upload photo_url (faster for dry runs).",
        )

    def handle(self, *args, **options):
        path = options["json_file"]

        try:
            with open(path, encoding="utf-8") as f:
                entries = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {path}")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON: {e}")

        if not isinstance(entries, list):
            raise CommandError("JSON root must be a list of person objects.")

        created_count = 0
        updated_count = 0
        error_count = 0

        for i, entry in enumerate(entries):
            label = f"{entry.get('first_name', '?')} {entry.get('last_name', '?')}"

            try:
                person, created = self.import_person(entry, skip_photos=options["skip_photos"])

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"[{i}] utworzono: {label}"))
                else:
                    updated_count += 1
                    self.stdout.write(f"[{i}] zaktualizowano: {label}")

            except Exception as e:
                error_count += 1
                self.stderr.write(self.style.ERROR(f"[{i}] blad przy {label}: {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"\nGotowe. Utworzono: {created_count}, zaktualizowano: {updated_count}, "
            f"bledy: {error_count}"
        ))

    def import_person(self, entry, skip_photos=False):
        first_name = entry["first_name"].strip()
        last_name = entry["last_name"].strip()

        try:
            person = Person.objects.get(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
            )
            created = False
        except Person.DoesNotExist:
            person = Person(first_name=first_name, last_name=last_name)
            created = True

        # Set every field (including city) before the first save() call -
        # Person.save() only geocodes on creation, and only if city is
        # already populated at that point.
        for field in (
            "position", "organization", "city", "voivodeship",
            "annual_salary", "salary_min", "salary_max",
            "party", "description",
        ):
            if field in entry:
                setattr(person, field, entry[field])

        photo_url = entry.get("photo_url")
        if photo_url and not skip_photos:
            self.attach_photo(person, photo_url)

        person.save()

        for source in entry.get("sources", []):
            PersonSource.objects.get_or_create(
                person=person,
                title=source["title"],
                url=source["url"],
            )

        for membership in entry.get("party_memberships", []):
            party, _ = Party.objects.get_or_create(
                name__iexact=membership["party"],
                defaults={"name": membership["party"]},
            )

            PartyMembership.objects.update_or_create(
                person=person,
                party=party,
                start_year=membership["start_year"],
                end_year=membership.get("end_year"),
                defaults={
                    "position": membership.get("position", ""),
                    "description": membership.get("description", ""),
                    "family_relation": membership.get("family_relation", ""),
                },
            )

        return person, created

    def attach_photo(self, person, photo_url):
        slug = slugify(f"{person.first_name}-{person.last_name}")

        try:
            result = cloudinary.uploader.upload(
                photo_url,
                public_id=f"people/{slug}",
                resource_type="image",
                overwrite=True,
            )
        except Exception as e:
            self.stderr.write(self.style.WARNING(
                f"  nie udalo sie pobrac/wgrac zdjecia ({photo_url}): {e}"
            ))
            return

        person.photo = CloudinaryResource(
            public_id=result["public_id"],
            format=result.get("format"),
            version=result.get("version"),
            resource_type=result.get("resource_type", "image"),
            type=result.get("type", "upload"),
        )
