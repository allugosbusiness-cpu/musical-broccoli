"""
Migration: Add optional fields that may be missing from production database.
These fields (max_speed, avg_speed, compressed_trail) are defined in the model 
but may not exist in the production database schema.

This migration adds them safely using Django's state operations.
The FleetMissionManager and serializer.create() both strip these fields 
during INSERT, so existing rows will get NULL/empty defaults.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fleetmission',
            name='max_speed',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fleetmission',
            name='avg_speed',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fleetmission',
            name='compressed_trail',
            field=models.JSONField(blank=True, default=list, help_text='Compressed list of [lat, lng, ts] for auditing'),
            preserve_default=True,
        ),
    ]