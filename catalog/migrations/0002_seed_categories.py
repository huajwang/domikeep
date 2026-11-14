from django.db import migrations

CATEGORIES = (
    ("Cameras", "cameras", 10),
    ("Alarms", "alarms", 20),
    ("Locks", "locks", 30),
    ("Lighting", "lighting", 40),
    ("Services", "services", 50),
)


def seed(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    for name, slug, sort_order in CATEGORIES:
        Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "sort_order": sort_order},
        )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
