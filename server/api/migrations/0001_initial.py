# First migration - clears old api app migration history and creates V2 tables
# All-in-one migration to avoid dependency issues

from django.db import migrations, models
import django.db.models.deletion
import uuid


def clear_old_migrations(apps, schema_editor):
    """Delete all old api app migrations from database"""
    from django.db import connection
    with connection.cursor() as cursor:
        try:
            # Clear all migrations from old 'api' app and any variants
            cursor.execute("DELETE FROM django_migrations WHERE app IN ('api', 'api.deprecated')")
            deleted = cursor.rowcount
            print(f"✅ Cleared {deleted} old api app migration record(s)")
        except Exception as e:
            # Table might not exist on first run
            print(f"ℹ️  Could not clear old migrations (table may not exist yet on first run)")


def drop_existing_v2_tables(apps, schema_editor):
    """Drop existing fleet tables to ensure clean creation"""
    from django.db import connection
    with connection.cursor() as cursor:
        tables_to_drop = [
            'fleet_admin_audit_logs',
            'fleet_driver_performance_daily',
            'fleet_dispute_comments',
            'fleet_disputes',
            'alerts',
            'fleet_activities',
            'fleet_truck_locations',
            'fleet_missions',
            'fleet_trucks',
            'fleet_drivers',
        ]
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"✅ Dropped table: {table}")
            except Exception as e:
                print(f"ℹ️  Could not drop {table}: {e}")


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        # Step 1: Clean up old migration records
        migrations.RunPython(clear_old_migrations, reverse_code=migrations.RunPython.noop),
        
        # Step 1b: Drop existing V2 tables to ensure clean creation
        migrations.RunPython(drop_existing_v2_tables, reverse_code=migrations.RunPython.noop),
        
        # Step 2: Create FleetDriver table
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
                ('performance_mark', models.DecimalField(db_index=True, decimal_places=2, default=0, max_digits=8)),
                ('deliveries_count', models.IntegerField(default=0)),
                ('last_active_at', models.DateTimeField(blank=True, null=True)),
                ('achievements', models.JSONField(blank=True, default=dict)),
                ('photo_url', models.URLField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'fleet_drivers'},
        ),
        
        # Step 3: Create FleetTruck table
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
            options={'db_table': 'fleet_trucks'},
        ),
        
        # Step 4: Add truck FK to FleetDriver
        migrations.AddField(
            model_name='fleetdriver',
            name='truck',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drivers', to='FleetTruck'),
        ),
        
        # Step 5: Create TruckLocation table
        migrations.CreateModel(
            name='TruckLocation',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('speed', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('accuracy', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('altitude', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('timestamp', models.DateTimeField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='location_history', to='FleetTruck')),
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='location_history', to='FleetDriver')),
            ],
            options={'db_table': 'fleet_truck_locations', 'ordering': ['-timestamp']},
        ),
        
        # Step 6: Create FleetMission table
        migrations.CreateModel(
            name='FleetMission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fleet_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('mission_number', models.CharField(db_index=True, max_length=50, unique=True)),
                ('status', models.CharField(choices=[('planned', 'Planned'), ('assigned', 'Assigned'), ('enroute', 'En Route'), ('paused', 'Paused'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], db_index=True, default='planned', max_length=20)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=20)),
                ('origin', models.JSONField(blank=True, default=dict)),
                ('destination', models.JSONField(blank=True, default=dict)),
                ('current_location', models.JSONField(blank=True, null=True)),
                ('route_polyline', models.TextField(blank=True, null=True)),
                ('distance_total_m', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12)),
                ('distance_remaining_m', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12)),
                ('progress_pct', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=5)),
                ('speed_kmh', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('eta', models.DateTimeField(blank=True, null=True)),
                ('cargo', models.JSONField(blank=True, default=dict)),
                ('stops', models.JSONField(blank=True, default=list)),
                ('mission_date', models.DateField(blank=True, db_index=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('created_by_admin_id', models.UUIDField(blank=True, null=True)),
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
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='missions', to='FleetDriver')),
                ('truck', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='missions', to='FleetTruck')),
            ],
            options={'db_table': 'fleet_missions'},
        ),
        
        # Step 7: Create Alert table
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('alert_type', models.CharField(choices=[('critical', 'Critical'), ('warning', 'Warning'), ('info', 'Info'), ('success', 'Success')], db_index=True, default='info', max_length=20)),
                ('message', models.TextField()),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], db_index=True, default='medium', max_length=20)),
                ('is_resolved', models.BooleanField(db_index=True, default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'alerts', 'ordering': ['-created_at']},
        ),
        
        # Step 8: Create FleetActivity table
        migrations.CreateModel(
            name='FleetActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fleet_id', models.UUIDField(db_index=True)),
                ('activity_type', models.CharField(choices=[('trail_recorded', 'Trail Recorded'), ('mission_created', 'Mission Created'), ('mission_started', 'Mission Started'), ('mission_paused', 'Mission Paused'), ('mission_resumed', 'Mission Resumed'), ('mission_completed', 'Mission Completed'), ('mission_cancelled', 'Mission Cancelled'), ('location_update', 'Location Update'), ('speed_recorded', 'Speed Recorded'), ('fuel_update', 'Fuel Update'), ('alert_triggered', 'Alert Triggered'), ('breach_detected', 'Breach Detected'), ('driver_check_in', 'Driver Check In'), ('driver_check_out', 'Driver Check Out'), ('maintenance_alert', 'Maintenance Alert'), ('speed_violation', 'Speed Violation'), ('geofence_breach', 'Geofence Breach'), ('stop_completed', 'Stop Completed'), ('cargo_update', 'Cargo Update'), ('distance_recorded', 'Distance Recorded'), ('other', 'Other')], db_index=True, default='other', max_length=50)),
                ('activity_category', models.CharField(choices=[('mission', 'Mission'), ('location', 'Location'), ('speed', 'Speed'), ('fuel', 'Fuel'), ('alert', 'Alert'), ('breach', 'Breach'), ('driver', 'Driver'), ('maintenance', 'Maintenance'), ('trail', 'Trail'), ('cargo', 'Cargo')], db_index=True, default='mission', max_length=20)),
                ('truck', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to='FleetTruck')),
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to='FleetDriver')),
                ('mission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to='FleetMission')),
                ('location_lat', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('location_lon', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('location_name', models.CharField(blank=True, max_length=255, null=True)),
                ('speed_kmh', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6, null=True)),
                ('distance_m', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12, null=True)),
                ('fuel_liters', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('fuel_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('alert_level', models.CharField(blank=True, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], max_length=20, null=True)),
                ('breach_type', models.CharField(blank=True, max_length=100, null=True)),
                ('violation_details', models.TextField(blank=True, null=True)),
                ('mission_status_before', models.CharField(blank=True, max_length=20, null=True)),
                ('mission_status_after', models.CharField(blank=True, max_length=20, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('activity_date', models.DateField(db_index=True)),
                ('activity_time', models.TimeField()),
                ('timestamp', models.DateTimeField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_critical', models.BooleanField(db_index=True, default=False)),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={'db_table': 'fleet_activities', 'ordering': ['-created_at']},
        ),
    ]
