# Generated migration to create V2 fleet management tables

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('server.api', '0001_initial'),
    ]

    operations = [
        # FleetDriver table
        migrations.CreateModel(
            name='FleetDriver',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fleet_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('first_name', models.CharField(db_index=True, max_length=100)),
                ('last_name', models.CharField(db_index=True, max_length=100)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('phone_number', models.CharField(blank=True, db_index=True, max_length=20, null=True, unique=True)),
                ('email', models.EmailField(blank=True, db_index=True, max_length=254, null=True, unique=True)),
                ('license_number', models.CharField(blank=True, db_index=True, max_length=50, null=True, unique=True)),
                ('license_state', models.CharField(blank=True, max_length=10, null=True)),
                ('hire_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended'), ('terminated', 'Terminated'), ('on_leave', 'On Leave')], db_index=True, default='active', max_length=20)),
                ('on_duty', models.BooleanField(db_index=True, default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('current_speed', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6, null=True)),
                ('last_location_update', models.DateTimeField(blank=True, null=True)),
                ('performance_mark', models.DecimalField(db_index=True, decimal_places=2, default=0, max_digits=8, validators=[])),
                ('deliveries_count', models.IntegerField(default=0)),
                ('last_active_at', models.DateTimeField(blank=True, null=True)),
                ('achievements', models.JSONField(blank=True, default=dict)),
                ('photo_url', models.URLField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'fleet_drivers',
            },
        ),
        # FleetTruck table
        migrations.CreateModel(
            name='FleetTruck',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fleet_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('truck_identifier', models.CharField(db_index=True, max_length=100, unique=True)),
                ('plate', models.CharField(db_index=True, max_length=20, unique=True)),
                ('vin', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('telematics_id', models.CharField(blank=True, db_index=True, max_length=100, null=True, unique=True)),
                ('make', models.CharField(blank=True, max_length=100, null=True)),
                ('model', models.CharField(blank=True, max_length=100, null=True)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('fuel_capacity_liters', models.DecimalField(decimal_places=2, default=100, max_digits=10)),
                ('fuel_consumed_liters', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('odometer_km', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('kilometers_travelled_km', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('status', models.CharField(choices=[('idle', 'Idle'), ('enroute', 'En Route'), ('maintenance', 'Maintenance'), ('decommissioned', 'Decommissioned')], db_index=True, default='idle', max_length=20)),
                ('is_moving', models.BooleanField(default=False)),
                ('last_latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('last_longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('last_location_ts', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'fleet_trucks',
            },
        ),
        # Add truck FK to FleetDriver
        migrations.AddField(
            model_name='fleetdriver',
            name='truck',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drivers', to='server.api.fleettruck'),
        ),
        # TruckLocation table
        migrations.CreateModel(
            name='TruckLocation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('altitude_m', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('speed_kmh', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('heading', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('accuracy_m', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locations', to='server.api.fleettruck')),
            ],
            options={
                'db_table': 'truck_locations',
                'ordering': ['-timestamp'],
            },
        ),
        # FleetMission table
        migrations.CreateModel(
            name='FleetMission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fleet_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('mission_number', models.CharField(db_index=True, max_length=50, unique=True)),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('assigned', 'Assigned'), ('enroute', 'En Route'), ('paused', 'Paused'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], db_index=True, default='planned', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=20)),
                ('pickup_address', models.CharField(blank=True, max_length=500, null=True)),
                ('pickup_latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('pickup_longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('delivery_address', models.CharField(blank=True, max_length=500, null=True)),
                ('delivery_latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('delivery_longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('cargo_description', models.TextField(blank=True)),
                ('cargo_weight_kg', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('cargo_volume_m3', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('estimated_distance_km', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('estimated_duration_minutes', models.IntegerField(blank=True, null=True)),
                ('actual_distance_km', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('actual_duration_minutes', models.IntegerField(blank=True, null=True)),
                ('planned_pickup', models.DateTimeField(blank=True, null=True)),
                ('actual_pickup', models.DateTimeField(blank=True, null=True)),
                ('planned_delivery', models.DateTimeField(blank=True, null=True)),
                ('actual_delivery', models.DateTimeField(blank=True, null=True)),
                ('cost_currency', models.CharField(blank=True, default='USD', max_length=3)),
                ('cost_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='missions', to='server.api.fleetdriver')),
                ('truck', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='missions', to='server.api.fleettruck')),
            ],
            options={
                'db_table': 'fleet_missions',
            },
        ),
        # Alert table
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
        # FleetActivity table
        migrations.CreateModel(
            name='FleetActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('activity_type', models.CharField(choices=[('trail_recorded', 'Trail Recorded'), ('mission_created', 'Mission Created'), ('mission_started', 'Mission Started'), ('mission_paused', 'Mission Paused'), ('mission_resumed', 'Mission Resumed'), ('mission_completed', 'Mission Completed'), ('mission_cancelled', 'Mission Cancelled'), ('location_update', 'Location Update'), ('speed_recorded', 'Speed Recorded'), ('fuel_update', 'Fuel Update'), ('alert_triggered', 'Alert Triggered'), ('breach_detected', 'Breach Detected'), ('driver_check_in', 'Driver Check In'), ('driver_check_out', 'Driver Check Out'), ('maintenance_alert', 'Maintenance Alert'), ('speed_violation', 'Speed Violation'), ('geofence_breach', 'Geofence Breach'), ('stop_completed', 'Stop Completed'), ('cargo_update', 'Cargo Update'), ('distance_recorded', 'Distance Recorded'), ('other', 'Other')], max_length=50)),
                ('description', models.TextField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'fleet_activities',
                'ordering': ['-created_at'],
            },
        ),
    ]
