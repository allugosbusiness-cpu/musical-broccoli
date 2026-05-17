# Generated migration file
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='truck',
            name='route_color',
            field=models.CharField(
                max_length=7,
                default='#3b82f6',
                help_text='Hex color for route visualization (e.g., #FF5733)'
            ),
        ),
        migrations.AddField(
            model_name='truck',
            name='route_geojson',
            field=models.JSONField(
                null=True,
                blank=True,
                default=dict,
                help_text='GeoJSON LineString geometry for the truck route'
            ),
        ),
        migrations.AddField(
            model_name='route',
            name='geometry',
            field=models.JSONField(
                null=True,
                blank=True,
                default=dict,
                help_text='GeoJSON LineString geometry from OSRM'
            ),
        ),
    ]
