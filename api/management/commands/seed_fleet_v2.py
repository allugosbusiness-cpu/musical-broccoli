from django.core.management.base import BaseCommand
from api.models_v2 import FleetTruck, FleetDriver, FleetMission
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
        
        # Create test driver
        test_driver_id = '570eb29f-ee89-4676-9d16-0fe7593ae8d8'
        try:
            driver = FleetDriver.objects.get(id=test_driver_id)
            self.stdout.write(self.style.WARNING(f'⚠ Test driver already exists: {driver.get_display_name()}'))
        except FleetDriver.DoesNotExist:
            driver = FleetDriver.objects.create(
                id=test_driver_id,
                fleet_id=test_fleet_id,
                phone_number='+256700000000',
                first_name='Test',
                last_name='Driver',
                email='test@example.com',
                truck=truck,
                is_active=True,
                on_duty=True
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created test driver: {driver.get_display_name()}'))
        
        # Create sample missions for testing
        sample_missions = [
            {
                'mission_number': 'MISSION-001',
                'status': 'planned',
                'origin': {'lat': 6.9271, 'lng': 33.7347},
                'destination': {'lat': 6.8, 'lng': 33.5},
                'distance_total_m': 12500,
                'cargo': {'item': 'Medical supplies', 'weight_kg': 150}
            },
            {
                'mission_number': 'MISSION-002',
                'status': 'planned',
                'origin': {'lat': 6.9271, 'lng': 33.7347},
                'destination': {'lat': 7.0, 'lng': 33.9},
                'distance_total_m': 18500,
                'cargo': {'item': 'Food items', 'weight_kg': 250}
            },
            {
                'mission_number': 'MISSION-003',
                'status': 'assigned',
                'origin': {'lat': 6.9271, 'lng': 33.7347},
                'destination': {'lat': 6.75, 'lng': 33.6},
                'distance_total_m': 25000,
                'cargo': {'item': 'Emergency supplies', 'weight_kg': 300}
            }
        ]
        
        for mission_data in sample_missions:
            if not FleetMission.objects.filter(mission_number=mission_data['mission_number']).exists():
                FleetMission.objects.create(
                    id=uuid.uuid4(),
                    fleet_id=test_fleet_id,
                    truck=truck,
                    driver=driver,
                    mission_number=mission_data['mission_number'],
                    status=mission_data['status'],
                    origin=mission_data['origin'],
                    destination=mission_data['destination'],
                    distance_total_m=mission_data['distance_total_m'],
                    cargo=mission_data['cargo']
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Created mission: {mission_data["mission_number"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Mission already exists: {mission_data["mission_number"]}'))
        
        self.stdout.write(self.style.SUCCESS(f'✓ Truck registered successfully - Ready for mission testing!'))
