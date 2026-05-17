# Generated migration for fuel tracking models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_merge_0002_add_route_fields_0006_add_ml_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='TruckFuel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('vehicle_type', models.CharField(choices=[('light_truck', 'Light Truck'), ('medium_truck', 'Medium Truck'), ('heavy_truck', 'Heavy Truck'), ('semi_truck', 'Semi Truck')], default='medium_truck', max_length=20)),
                ('tank_capacity_liters', models.FloatField(default=100)),
                ('current_fuel_liters', models.FloatField(default=100)),
                ('fuel_efficiency_kmpl', models.FloatField(default=0.1)),
                ('warning_level_percent', models.IntegerField(default=25)),
                ('critical_level_percent', models.IntegerField(default=10)),
                ('total_fuel_consumed_liters', models.FloatField(default=0)),
                ('total_distance_traveled_km', models.FloatField(default=0)),
                ('last_refuel_date', models.DateTimeField(blank=True, null=True)),
                ('last_refuel_amount', models.FloatField(blank=True, null=True)),
                ('needs_refuel', models.BooleanField(default=False)),
                ('is_low_fuel', models.BooleanField(default=False)),
                ('is_critical_fuel', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('truck', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fuel_info', to='api.truck')),
            ],
            options={
                'db_table': 'truck_fuel',
            },
        ),
        migrations.CreateModel(
            name='FuelConsumption',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('consumption_type', models.CharField(choices=[('segment', 'Route Segment'), ('trip', 'Complete Trip'), ('idle', 'Idle Time'), ('refuel', 'Refuel Event')], default='segment', max_length=20)),
                ('consumption_liters', models.FloatField()),
                ('distance_km', models.FloatField(default=0)),
                ('duration_minutes', models.IntegerField(default=0)),
                ('avg_speed_kmh', models.FloatField(default=0)),
                ('elevation_gain_m', models.FloatField(default=0)),
                ('elevation_loss_m', models.FloatField(default=0)),
                ('load_percent', models.FloatField(default=50)),
                ('weather_conditions', models.JSONField(default=dict)),
                ('efficiency_kmpl', models.FloatField(default=0)),
                ('efficiency_mpg', models.FloatField(default=0)),
                ('fuel_before_liters', models.FloatField()),
                ('fuel_after_liters', models.FloatField()),
                ('consumption_factors', models.JSONField(default=dict)),
                ('start_timestamp', models.DateTimeField()),
                ('end_timestamp', models.DateTimeField()),
                ('was_predicted', models.BooleanField(default=False)),
                ('actual_vs_predicted_percent', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('route', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fuel_consumption', to='api.route')),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fuel_consumption', to='api.truck')),
            ],
            options={
                'db_table': 'fuel_consumption',
                'ordering': ['-start_timestamp'],
            },
        ),
        migrations.CreateModel(
            name='FuelRefuel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount_liters', models.FloatField()),
                ('cost_usd', models.FloatField(default=0)),
                ('location', models.CharField(max_length=100)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('fuel_before_liters', models.FloatField()),
                ('fuel_after_liters', models.FloatField()),
                ('fuel_price_per_liter', models.FloatField(blank=True, null=True)),
                ('refuel_timestamp', models.DateTimeField()),
                ('duration_minutes', models.IntegerField(default=5)),
                ('driver_name', models.CharField(blank=True, max_length=100)),
                ('driver_notes', models.TextField(blank=True)),
                ('fuel_efficiency_kmpl_before', models.FloatField(blank=True, null=True)),
                ('distance_since_last_refuel_km', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refuel_events', to='api.truck')),
            ],
            options={
                'db_table': 'fuel_refuel',
                'ordering': ['-refuel_timestamp'],
            },
        ),
        migrations.CreateModel(
            name='FuelAlert',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('alert_type', models.CharField(max_length=50)),
                ('severity', models.CharField(choices=[('info', 'Information'), ('warning', 'Warning'), ('critical', 'Critical')], default='warning', max_length=20)),
                ('message', models.TextField()),
                ('current_fuel_liters', models.FloatField()),
                ('current_fuel_percent', models.FloatField()),
                ('estimated_range_km', models.FloatField()),
                ('is_acknowledged', models.BooleanField(default=False)),
                ('is_resolved', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('resolution_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fuel_alerts', to='api.truck')),
            ],
            options={
                'db_table': 'fuel_alerts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='fuelrefuel',
            index=models.Index(fields=['truck', '-refuel_timestamp'], name='fuel_refuel_truck_id_refuel_d_idx'),
        ),
        migrations.AddIndex(
            model_name='fuelconsumption',
            index=models.Index(fields=['truck', '-start_timestamp'], name='fuel_consumption_truck_id_start_idx'),
        ),
        migrations.AddIndex(
            model_name='fuelconsumption',
            index=models.Index(fields=['route', 'start_timestamp'], name='fuel_consumption_route_id_start_idx'),
        ),
    ]
