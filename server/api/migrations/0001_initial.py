# First migration - clears old api app migration history and creates empty initial state
# The actual models will be created by Django's table creation

from django.db import migrations, models


def delete_old_migrations(apps, schema_editor):
    """Delete all old api app migrations from database"""
    from django.db import connection
    with connection.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'api'")
            print(f"✅ Cleared old api app migration history")
        except Exception as e:
            print(f"⚠️ Could not clear old api migrations: {e}")


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.RunPython(delete_old_migrations, reverse_code=migrations.RunPython.noop),
    ]
