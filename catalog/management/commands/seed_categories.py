from django.core.management.base import BaseCommand

from catalog.models import Category

CATEGORIES = (
    ("Cameras", "cameras", 10),
    ("Alarms", "alarms", 20),
    ("Locks", "locks", 30),
    ("Lighting", "lighting", 40),
    ("Services", "services", 50),
)


class Command(BaseCommand):
    help = "Create the empty shop categories."

    def handle(self, *args, **options):
        for name, slug, sort_order in CATEGORIES:
            _, created = Category.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "sort_order": sort_order},
            )
            self.stdout.write(f"{'created' if created else 'kept'} {slug}")
