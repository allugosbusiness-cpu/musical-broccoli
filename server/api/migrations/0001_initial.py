# Generated migration for PulseTrack V2 Fleet Management

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        # FleetDriver
        migrations.CreateModel(
            name='FleetDriver',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('phone_number', models.CharField(max_length=15, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended'), ('terminated', 'Terminated'), ('on_leave', 'On Leave')], default='active', max_length=20)),
                ('license_number', models.CharField(blank=True, max_length=50, null=True)),
                ('license_expiry', models.DateField(blank=True, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('hire_date', models.DateField(auto_now_add=True)),
                ('performance_mark', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'fleet_drivers',
                'ordering': ['-created_at'],
            },
        ),
        # FleetTruck
        migrations.CreateModel(
            name='FleetTruck',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('plate_number', models.CharField(max_length=20, unique=True)),
                ('vehicle_type', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[('idle', 'Idle'), ('enroute', 'En Route'), ('maintenance', 'Maintenance'), ('decommissioned', 'Decommissioned')], default='idle', max_length=20)),
                ('current_location', models.JSONField(default=dict)),
                ('speed_kmh', models.FloatField(default=0.0)),
                ('fuel_level', models.FloatField(blank=True, default=100, null=True)),
                ('mileage', models.FloatField(default=0.0)),
                ('color', models.CharField(blank=True, default='#3498db', max_length=10, null=True)),
                ('capacity_tons', models.FloatField(blank=True, null=True)),
                ('manufacturing_year', models.IntegerField(blank=True, null=True)),
                ('registration_date', models.DateField(blank=True, null=True)),
                ('auto_routing_enabled', models.BooleanField(default=True)),
                ('current_route', models.JSONField(blank=True, default=list, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'fleet_trucks',
                'ordering': ['-created_at'],
            },
        ),
        # TruckLocation
        migrations.CreateModel(
            name='TruckLocation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('speed_kmh', models.FloatField(default=0.0)),
                ('accuracy', models.FloatField(blank=True, null=True)),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locations', to='server.api.fleettruck')),
            ],
            options={
                'db_table': 'truck_locations',
                'ordering': ['-timestamp'],
                'indexes': [
                    models.Index(fields=['truck', '-timestamp'], name='truck_loc_idx'),
                ],
            },
        ),
        # FleetMission
        migrations.CreateModel(
            name='FleetMission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('assigned', 'Assigned'), ('enroute', 'En Route'), ('paused', 'Paused'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='planned', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=20)),
                ('cargo_description', models.TextField(blank=True)),
                ('cargo_weight_tons', models.FloatField(blank=True, null=True)),
                ('estimated_distance_km', models.FloatField(blank=True, null=True)),
                ('estimated_duration_minutes', models.IntegerField(blank=True, null=True)),
                ('actual_distance_km', models.FloatField(blank=True, null=True)),
                ('actual_duration_minutes', models.IntegerField(blank=True, null=True)),
                ('planned_start', models.DateTimeField(blank=True, null=True)),
                ('actual_start', models.DateTimeField(blank=True, null=True)),
                ('planned_end', models.DateTimeField(blank=True, null=True)),
                ('actual_end', models.DateTimeField(blank=True, null=True)),
                ('mission_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='missions', to='server.api.fleetdriver')),
                ('truck', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='missions', to='server.api.fleettruck')),
            ],
            options={
                'db_table': 'fleet_missions',
                'ordering': ['-created_at'],
            },
        ),
        # FleetMissionStop
        migrations.CreateModel(
            name='FleetMissionStop',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('sequence', models.IntegerField()),
                ('location_name', models.CharField(max_length=200)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('skipped', 'Skipped')], default='pending', max_length=20)),
                ('planned_arrival', models.DateTimeField(blank=True, null=True)),
                ('actual_arrival', models.DateTimeField(blank=True, null=True)),
                ('planned_departure', models.DateTimeField(blank=True, null=True)),
                ('actual_departure', models.DateTimeField(blank=True, null=True)),
                ('stop_duration_minutes', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stops', to='server.api.fleettmission')),
            ],
            options={
                'db_table': 'fleet_mission_stops',
                'ordering': ['sequence'],
            },
        ),
        # Alert
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('alert_type', models.CharField(choices=[('critical', 'Critical'), ('warning', 'Warning'), ('info', 'Info'), ('success', 'Success')], default='info', max_length=20)),
                ('message', models.TextField()),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=20)),
                ('is_resolved', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'alerts',
                'ordering': ['-created_at'],
            },
        ),
        # FleetActivity
        migrations.CreateModel(
            name='FleetActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('activity_type', models.CharField(choices=[('trail_recorded', 'Trail Recorded'), ('mission_created', 'Mission Created'), ('mission_started', 'Mission Started'), ('mission_paused', 'Mission Paused'), ('mission_resumed', 'Mission Resumed'), ('mission_completed', 'Mission Completed'), ('mission_cancelled', 'Mission Cancelled'), ('location_update', 'Location Update'), ('speed_recorded', 'Speed Recorded'), ('fuel_update', 'Fuel Update'), ('alert_triggered', 'Alert Triggered'), ('breach_detected', 'Breach Detected'), ('driver_check_in', 'Driver Check In'), ('driver_check_out', 'Driver Check Out'), ('maintenance_alert', 'Maintenance Alert'), ('speed_violation', 'Speed Violation'), ('geofence_breach', 'Geofence Breach'), ('stop_completed', 'Stop Completed'), ('cargo_update', 'Cargo Update'), ('distance_recorded', 'Distance Recorded'), ('other', 'Other')], max_length=50)),
                ('description', models.TextField()),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'fleet_activities',
                'ordering': ['-created_at'],
            },
        ),
    ]
