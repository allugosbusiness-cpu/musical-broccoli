# First migration - clears old api app migration history
# Django will auto-create tables from models after this migration runs

from django.db import migrations


def clear_old_migrations(apps, schema_editor):
    """Delete all old api app migrations from database"""
    from django.db import connection
    with connection.cursor() as cursor:
        try:
            # This will fail if table doesn't exist yet (first run), which is fine
            cursor.execute("DELETE FROM django_migrations WHERE app = 'api'")
            deleted = cursor.rowcount
            print(f"✅ Cleared {deleted} old api app migration record(s)")
        except Exception as e:
            print(f"ℹ️  Migration history table not yet created (expected on first run)")


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        # Run the cleanup first
        migrations.RunPython(clear_old_migrations, reverse_code=migrations.RunPython.noop),
    ]
