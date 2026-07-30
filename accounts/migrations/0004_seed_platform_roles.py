from django.db import migrations


ROLE_DESCRIPTIONS = {
    "customer": "Requests services on the platform.",
    "driver": "Provides mobility and delivery services.",
    "merchant": "Operates a shop or commerce branch.",
    "property_owner": "Lists accommodation or rental property.",
    "employer": "Posts jobs and reviews applications.",
    "admin": "Operates and governs the platform.",
    "support": "Handles customer and provider support.",
}


def seed_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    for name, description in ROLE_DESCRIPTIONS.items():
        Role.objects.update_or_create(
            name=name,
            defaults={"description": description},
        )


def unseed_roles(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(name__in=ROLE_DESCRIPTIONS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_accountrole_status"),
    ]

    operations = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]
