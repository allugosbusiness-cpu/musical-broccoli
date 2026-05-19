# Generated: Fresh V2 consolidated migration - mobile + web unified
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FleetDriver',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fleet_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('first_name', models.CharField(db_index=True, max_length=100)),
                ('last_name', models.CharField(db_index=True, max_length=100)),
                ('phone_number', models.CharField(blank=True, db_index=True, max_length=20, null=True, unique=True)),
                ('email', models.EmailField(blank=True, db_index=True, max_length=254, null=True, unique=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended'), ('terminated', 'Terminated'), ('on_leave', 'On Leave')], db_index=True, default='active', max_length=20)),
                ('on_duty', models.BooleanField(db_index=True, default=False)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('performance_mark', models.DecimalField(db_index=True, decimal_places=2, default=0, max_digits=8)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'fleet_drivers'},
        ),
        migrations.CreateModel(
            name='FleetTruck',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fleet_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('truck_identifier', models.CharField(db_index=True, max_length=100, unique=True)),
                ('plate', models.CharField(db_index=True, max_length=20, unique=True)),
                ('vin', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                ('telematics_id', models.CharField(blank=True, db_index=True, max_length=100, null=True, unique=True)),
                ('fuel_capacity_liters', models.DecimalField(decimal_places=2, default=100, max_digits=10)),
                ('fuel_consumed_liters', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('odometer_km', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('status', models.CharField(choices=[('idle', 'Idle'), ('enroute', 'En Route'), ('maintenance', 'Maintenance'), ('decommissioned', 'Decommissioned')], db_index=True, default='idle', max_length=20)),
                ('last_latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('last_longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('last_location_ts', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'fleet_trucks'},
        ),
        migrations.AddField(
            model_name='fleetdriver',
            name='truck',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drivers', to='api.fleettruck'),
        ),
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
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='location_history', to='api.fleetdriver')),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='location_history', to='api.fleettruck')),
            ],
            options={'db_table': 'fleet_truck_locations', 'ordering': ['-timestamp']},
        ),
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
                ('distance_total_m', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=12)),
                ('progress_pct', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=5)),
                ('cargo', models.JSONField(blank=True, default=dict)),
                ('mission_date', models.DateField(blank=True, db_index=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('max_speed', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6)),
                ('avg_speed', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=6)),
                ('compressed_trail', models.JSONField(blank=True, default=list, help_text='Compressed list of [lat, lng, ts] for auditing')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='missions', to='api.fleetdriver')),
                ('truck', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='missions', to='api.fleettruck')),
            ],
            options={'db_table': 'fleet_missions'},
        ),
        migrations.CreateModel(
            name='FleetActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('activity_type', models.CharField(choices=[('start', 'Start'), ('stop', 'Stop'), ('pause', 'Pause'), ('resume', 'Resume'), ('complete', 'Complete'), ('other', 'Other')], db_index=True, default='other', max_length=20)),
                ('activity_category', models.CharField(default='mission', max_length=50)),
                ('description', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to='api.fleetdriver')),
                ('mission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to='api.fleetmission')),
                ('truck', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to='api.fleettruck')),
            ],
            options={'db_table': 'fleet_activities'},
        ),
        migrations.CreateModel(
            name='FleetDriverPerformanceDaily',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(db_index=True)),
                ('missions_completed', models.IntegerField(default=0)),
                ('distance_km', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('hours_on_duty', models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ('rating', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=3, null=True)),
                ('incidents', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_performance', to='api.fleetdriver')),
            ],
            options={'db_table': 'fleet_driver_performance_daily'},
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('alert_type', models.CharField(choices=[('speed', 'Speeding'), ('temperature', 'Temperature'), ('maintenance', 'Maintenance'), ('location', 'Location'), ('delivery', 'Delivery'), ('other', 'Other')], db_index=True, max_length=50)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], db_index=True, max_length=20)),
                ('message', models.TextField()),
                ('is_resolved', models.BooleanField(db_index=True, default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'alerts'},
        ),
    ]
