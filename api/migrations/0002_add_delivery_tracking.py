# Generated migration for adding delivery tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),  # Adjust to match your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='fleetmission',
            name='delivered_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
