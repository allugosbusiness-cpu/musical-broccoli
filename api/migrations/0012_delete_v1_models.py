# Delete all v1 table data and recommend using v2 models only

from django.db import migrations

def delete_v1_data(apps, schema_editor):
    """Delete all data from v1 models to migrate to v2"""
    # Get the v1 models
    models_to_clear = [
        'Truck', 'Checkpoint', 'Cargo', 'Alert', 'KPI', 
        'Route', 'Location', 'CurrentLocation', 'TrackPoint', 
        'RouteOptimization'
    ]
    
    for model_name in models_to_clear:
        try:
            Model = apps.get_model('api', model_name)
            deleted_count, _ = Model.objects.all().delete()
            print(f"✓ Deleted {deleted_count} records from {model_name}")
        except LookupError:
            print(f"✗ Model {model_name} not found")
        except Exception as e:
            print(f"✗ Error clearing {model_name}: {e}")

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_alter_fleetdriver_performance_mark'),
    ]

    operations = [
        # Delete all v1 table data - migration to v2 models only
        migrations.RunPython(delete_v1_data),
    ]
