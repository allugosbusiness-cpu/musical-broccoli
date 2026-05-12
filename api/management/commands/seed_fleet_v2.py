from django.core.management.base import BaseCommand
from api.models_v2 import FleetTruck, FleetDriver
import uuid

class Command(BaseCommand):
    help = 'Seed database with v2 fleet data for testing'

    def handle(self, *args, **options):
        # Use a consistent test fleet ID
        test_fleet_id = uuid.UUID('12345678-1234-1234-1234-123456789012')
        
        # Create or update the specific truck from the QR code
        truck_data = {
            'fleet_id': test_fleet_id,
            'truck_identifier': 'SCANNER_TEST',
            'plate': 'ZWE-TEST-1',
            'make': 'Hino',
            'model': '500 Series',
            'year': 2022,
            'status': 'idle',
            'is_moving': False,
            'fuel_capacity_liters': 150,
            'speed_kmh': 0,
        }
        
        truck_uuid = '6f91a80d-eecd-47c5-a4ac-0b546b9cb473'
        
        try:
            truck = FleetTruck.objects.get(id=truck_uuid)
            # Update existing truck
            for key, value in truck_data.items():
                setattr(truck, key, value)
            truck.save()
            self.stdout.write(self.style.WARNING(f'⚠ Updated existing truck: {truck.truck_identifier}'))
        except FleetTruck.DoesNotExist:
            # Create new truck with specific UUID
            truck = FleetTruck.objects.create(
                id=truck_uuid,
                **truck_data
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created truck: {truck.truck_identifier}'))
        
        self.stdout.write(self.style.SUCCESS(f'✓ Truck ID: {truck.id}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Fleet ID: {truck.fleet_id}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Truck registered successfully - Ready for QR code registration!'))
