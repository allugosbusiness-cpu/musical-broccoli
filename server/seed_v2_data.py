#!/usr/bin/env python
"""
Seed database with sample v2 fleet data
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models_v2 import FleetTruck, FleetDriver
import uuid

# Clear existing data
FleetTruck.objects.all().delete()
FleetDriver.objects.all().delete()

fleet_id = uuid.uuid4()

# Sample drivers
drivers_data = [
    {
        'fleet_id': fleet_id,
        'first_name': 'John',
        'last_name': 'Ndlela',
        'phone_number': '+263712345678',
        'license_number': 'DL123456',
        'status': 'active',
        'on_duty': True,
        'is_active': True,
    },
    {
        'fleet_id': fleet_id,
        'first_name': 'Grace',
        'last_name': 'Mwale',
        'phone_number': '+263712345679',
        'license_number': 'DL123457',
        'status': 'active',
        'on_duty': True,
        'is_active': True,
    },
]

drivers = []
for driver_data in drivers_data:
    driver = FleetDriver.objects.create(**driver_data)
    drivers.append(driver)
    print(f"✓ Created driver: {driver.get_display_name()}")

# Sample trucks
trucks_data = [
    {
        'fleet_id': fleet_id,
        'truck_identifier': 'TRK1',
        'plate': 'AXE5422',
        'make': 'Hino',
        'model': '500 Series',
        'year': 2022,
        'status': 'idle',
        'is_moving': False,
        'fuel_capacity_liters': 150,
        'current_location': {'lat': -17.8252, 'lon': 31.0335, 'timestamp': '2026-05-11T00:00:00Z'},
        'speed_kmh': 0,
    },
    {
        'fleet_id': fleet_id,
        'truck_identifier': 'TRK2',
        'plate': 'ZWE-1001',
        'make': 'Volvo',
        'model': 'FH16',
        'year': 2021,
        'status': 'idle',
        'is_moving': False,
        'fuel_capacity_liters': 250,
        'current_location': {'lat': -20.1500, 'lon': 28.5800, 'timestamp': '2026-05-11T00:00:00Z'},
        'speed_kmh': 0,
    },
    {
        'fleet_id': fleet_id,
        'truck_identifier': 'TRK3',
        'plate': 'ATY 3272',
        'make': 'Scania',
        'model': 'R440',
        'year': 2020,
        'status': 'idle',
        'is_moving': False,
        'fuel_capacity_liters': 200,
        'current_location': {'lat': -18.9704, 'lon': 32.6648, 'timestamp': '2026-05-11T00:00:00Z'},
        'speed_kmh': 0,
    },
    {
        'fleet_id': fleet_id,
        'truck_identifier': 'TRK4',
        'plate': 'AQW7645',
        'make': 'MAN',
        'model': 'TGX',
        'year': 2023,
        'status': 'idle',
        'is_moving': False,
        'fuel_capacity_liters': 200,
        'current_location': {'lat': -20.2631, 'lon': 30.8276, 'timestamp': '2026-05-11T00:00:00Z'},
        'speed_kmh': 0,
    },
]

trucks = []
for i, truck_data in enumerate(trucks_data):
    truck = FleetTruck.objects.create(**truck_data)
    if i < len(drivers):
        truck.assigned_driver = drivers[i]
        truck.save()
    trucks.append(truck)
    print(f"✓ Created truck: {truck.truck_identifier} ({truck.plate})")

print(f"\n✓ Sample data seeded successfully!")
print(f"  - {len(drivers)} drivers")
print(f"  - {len(trucks)} trucks")
print(f"  - Fleet ID: {fleet_id}")
