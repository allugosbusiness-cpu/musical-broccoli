# Generated migration for ML-based routing models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_trackpoint'),
    ]

    operations = [
        # Create Location model
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('address', models.TextField(blank=True)),
                ('location_type', models.CharField(
                    choices=[
                        ('warehouse', 'Warehouse'),
                        ('delivery', 'Delivery Point'),
                        ('checkpoint', 'Checkpoint'),
                        ('hub', 'Distribution Hub'),
                        ('station', 'Service Station'),
                        ('other', 'Other')
                    ],
                    default='other',
                    max_length=20
                )),
                ('average_dwell_time_minutes', models.FloatField(default=0)),
                ('congestion_factor', models.FloatField(default=1.0)),
                ('accessibility_score', models.FloatField(default=1.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'locations',
            },
        ),
        
        # Add foreign keys to Truck model
        migrations.AddField(
            model_name='truck',
            name='origin_location',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='trucks_starting_here',
                to='api.location'
            ),
        ),
        migrations.AddField(
            model_name='truck',
            name='destination_location',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='trucks_going_here',
                to='api.location'
            ),
        ),
        
        # Create CurrentLocation model
        migrations.CreateModel(
            name='CurrentLocation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('speed', models.FloatField(default=0)),
                ('heading', models.FloatField(blank=True, null=True)),
                ('altitude', models.FloatField(blank=True, null=True)),
                ('accuracy', models.FloatField(blank=True, null=True)),
                ('predicted_next_location', models.JSONField(default=dict)),
                ('predicted_arrival_time', models.DateTimeField(blank=True, null=True)),
                ('predicted_fuel_consumption_liters', models.FloatField(default=0)),
                ('traffic_ahead', models.JSONField(default=dict)),
                ('distance_to_next_checkpoint_km', models.FloatField(default=0)),
                ('distance_to_destination_km', models.FloatField(default=0)),
                ('time_to_destination_minutes', models.FloatField(default=0)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('recorded_at', models.DateTimeField()),
                ('truck', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='current_location',
                    to='api.truck'
                )),
            ],
            options={
                'db_table': 'current_locations',
            },
        ),
        
        # Create RouteOptimization model
        migrations.CreateModel(
            name='RouteOptimization',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('original_distance_km', models.FloatField()),
                ('optimized_distance_km', models.FloatField()),
                ('distance_saved_percent', models.FloatField()),
                ('original_time_hours', models.FloatField()),
                ('optimized_time_hours', models.FloatField()),
                ('time_saved_percent', models.FloatField()),
                ('estimated_fuel_liters', models.FloatField()),
                ('fuel_cost_estimated', models.FloatField()),
                ('co2_emissions_kg', models.FloatField(default=0)),
                ('alternative_routes', models.JSONField(default=list)),
                ('model_version', models.CharField(default='v1.0', max_length=50)),
                ('confidence_score', models.FloatField(default=0.8)),
                ('reasoning', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('truck', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='optimizations',
                    to='api.truck'
                )),
                ('route', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='optimization',
                    to='api.route'
                )),
            ],
            options={
                'db_table': 'route_optimizations',
                'ordering': ['-created_at'],
            },
        ),
        
        # Add index to Location
        migrations.AddIndex(
            model_name='location',
            index=models.Index(fields=['name'], name='locations_name_idx'),
        ),
        migrations.AddIndex(
            model_name='location',
            index=models.Index(fields=['location_type'], name='locations_type_idx'),
        ),
    ]
