"""
Django management command to populate the Location table with Zimbabwe locations
"""

from django.core.management.base import BaseCommand
from api.models import Location

LOCATIONS_DATA = [
    {
        'name': 'Harare',
        'latitude': -17.8252,
        'longitude': 31.0335,
        'address': 'Zimbabwe',
        'location_type': 'hub',
        'average_dwell_time_minutes': 120,
        'congestion_factor': 1.3,
        'accessibility_score': 0.95,
    },
    {
        'name': 'Bulawayo',
        'latitude': -20.1503,
        'longitude': 28.2803,
        'address': 'Zimbabwe',
        'location_type': 'hub',
        'average_dwell_time_minutes': 100,
        'congestion_factor': 1.1,
        'accessibility_score': 0.90,
    },
    {
        'name': 'Mutare',
        'latitude': -18.9700,
        'longitude': 32.6656,
        'address': 'Zimbabwe',
        'location_type': 'delivery',
        'average_dwell_time_minutes': 60,
        'congestion_factor': 1.0,
        'accessibility_score': 0.85,
    },
    {
        'name': 'Gweru',
        'latitude': -19.4537,
        'longitude': 29.8147,
        'address': 'Zimbabwe',
        'location_type': 'checkpoint',
        'average_dwell_time_minutes': 45,
        'congestion_factor': 0.9,
        'accessibility_score': 0.88,
    },
    {
        'name': 'Kadoma',
        'latitude': -18.3333,
        'longitude': 29.9167,
        'address': 'Zimbabwe',
        'location_type': 'warehouse',
        'average_dwell_time_minutes': 90,
        'congestion_factor': 0.95,
        'accessibility_score': 0.92,
    },
    {
        'name': 'Chinhoyi',
        'latitude': -17.7667,
        'longitude': 30.2167,
        'address': 'Zimbabwe',
        'location_type': 'checkpoint',
        'average_dwell_time_minutes': 30,
        'congestion_factor': 0.85,
        'accessibility_score': 0.90,
    },
    {
        'name': 'Kariba',
        'latitude': -17.4667,
        'longitude': 26.8667,
        'address': 'Zimbabwe',
        'location_type': 'delivery',
        'average_dwell_time_minutes': 80,
        'congestion_factor': 1.2,
        'accessibility_score': 0.70,
    },
    {
        'name': 'Victoria Falls',
        'latitude': -17.9283,
        'longitude': 25.8544,
        'address': 'Zimbabwe',
        'location_type': 'delivery',
        'average_dwell_time_minutes': 120,
        'congestion_factor': 1.4,
        'accessibility_score': 0.75,
    },
    {
        'name': 'Masvingo',
        'latitude': -20.0667,
        'longitude': 30.8667,
        'address': 'Zimbabwe',
        'location_type': 'warehouse',
        'average_dwell_time_minutes': 75,
        'congestion_factor': 0.95,
        'accessibility_score': 0.87,
    },
    {
        'name': 'Harare Central Warehouse',
        'latitude': -17.8260,
        'longitude': 31.0345,
        'address': 'Harare City Centre, Zimbabwe',
        'location_type': 'warehouse',
        'average_dwell_time_minutes': 150,
        'congestion_factor': 1.5,
        'accessibility_score': 0.92,
    },
]


class Command(BaseCommand):
    help = 'Populate the Location table with Zimbabwe locations'

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        
        for loc_data in LOCATIONS_DATA:
            location, created = Location.objects.update_or_create(
                name=loc_data['name'],
                defaults=loc_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created location: {location.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⟳ Updated location: {location.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
