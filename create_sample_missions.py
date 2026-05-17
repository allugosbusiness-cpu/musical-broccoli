#!/usr/bin/env python
"""
Create sample missions for testing the mission selection feature
Run: python create_sample_missions.py
"""
import os
import django
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Logistics.settings")
django.setup()

from api.models_v2 import FleetDriver, FleetTruck, FleetMission

# Get the test truck (from seed_fleet_v2)
test_truck_id = "6f91a80d-eecd-47c5-a4ac-0b546b9cb473"
test_driver_id = "570eb29f-ee89-4676-9d16-0fe7593ae8d8"

try:
    truck = FleetTruck.objects.get(id=test_truck_id)
    print(f"✅ Found test truck: {truck.truck_identifier}")
except FleetTruck.DoesNotExist:
    print(f"❌ Test truck not found: {test_truck_id}")
    exit(1)

try:
    driver = FleetDriver.objects.get(id=test_driver_id)
    print(f"✅ Found test driver: {driver.get_display_name()}")
except FleetDriver.DoesNotExist:
    # Create a test driver if it doesn't exist
    print(f"⚠️  Test driver not found, creating one...")
    driver = FleetDriver.objects.create(
        id=test_driver_id,
        fleet_id=truck.fleet_id,
        phone_number="+256700000000",
        first_name="Test",
        last_name="Driver",
        email="test@example.com",
        truck=truck,
        is_active=True,
        on_duty=True
    )
    print(f"✅ Created test driver: {driver.get_display_name()}")

# Create 3 sample missions
missions_to_create = [
    {
        'mission_number': 'MISSION-001',
        'status': 'planned',
        'origin': {'lat': 6.9271, 'lng': 33.7347},  # Kampala, Uganda
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

created_count = 0
for mission_data in missions_to_create:
    # Check if mission already exists
    if FleetMission.objects.filter(mission_number=mission_data['mission_number']).exists():
        print(f"⚠️  Mission {mission_data['mission_number']} already exists, skipping")
        continue
    
    mission = FleetMission.objects.create(
        id=uuid.uuid4(),
        fleet_id=truck.fleet_id,
        truck=truck,
        driver=driver,
        mission_number=mission_data['mission_number'],
        status=mission_data['status'],
        origin=mission_data['origin'],
        destination=mission_data['destination'],
        distance_total_m=mission_data['distance_total_m'],
        cargo=mission_data['cargo']
    )
    print(f"✅ Created mission: {mission.mission_number} ({mission.status})")
    created_count += 1

print(f"\n✅ Created {created_count} sample missions")
print(f"📊 Test driver can now select from available missions")
