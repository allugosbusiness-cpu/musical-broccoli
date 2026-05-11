# server/api/migrations/0013_add_mobile_tracking_models.py

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_delete_v1_models'),
    ]

    operations = [
        # Add fields to FleetDriver for mobile tracking
        migrations.AddField(
            model_name='fleetdriver',
            name='phone_number',
            field=models.CharField(blank=True, db_index=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='fleetdriver',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='fleetdriver',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='fleetdriver',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='fleetdriver',
            name='current_speed',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='fleetdriver',
            name='last_location_update',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='fleetdriver',
            name='truck',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drivers', to='api.fleettruck'),
        ),
        
        # Create TruckLocation model
        migrations.CreateModel(
            name='TruckLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('speed', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('accuracy', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('altitude', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('timestamp', models.DateTimeField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='location_history', to='api.fleetdriver')),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='location_history', to='api.fleettruck')),
            ],
            options={
                'db_table': 'fleet_truck_locations',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Add indexes for TruckLocation
        migrations.AddIndex(
            model_name='trucklocation',
            index=models.Index(fields=['truck', 'timestamp'], name='fleet_loc_truck_ts_idx'),
        ),
        migrations.AddIndex(
            model_name='trucklocation',
            index=models.Index(fields=['driver', 'timestamp'], name='fleet_loc_drv_ts_idx'),
        ),
        migrations.AddIndex(
            model_name='trucklocation',
            index=models.Index(fields=['-timestamp'], name='fleet_loc_timestamp_idx'),
        ),
    ]
