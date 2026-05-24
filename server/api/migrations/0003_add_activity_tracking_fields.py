"""
Migration: Add tracking fields to FleetActivity for mission performance audit trail.
These fields store average speed and compressed GPS trail per mission completion.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_add_missing_optional_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='fleetactivity',
            name='avg_speed',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fleetactivity',
            name='compressed_trail',
            field=models.JSONField(blank=True, default=list, help_text='Compressed GPS trail [lat, lng, timestamp] points for mission'),
            preserve_default=True,
        ),
    ]
