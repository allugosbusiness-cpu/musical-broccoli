#!/usr/bin/env python
"""
Seed database with sample fleet data after migrations
This ensures the API endpoints have data to return
"""

import os
import django
import uuid
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models_v2 import FleetDriver, FleetTruck, FleetMission, FleetMissionStop
from django.db import transaction

@transaction.atomic
def seed_fleet_data():
    """Seed the database with sample fleet data"""
    
    # Create drivers
    drivers_data = [
        {
            'first_name': 'John',
            'last_name': 'Driver',
            'phone': '+1234567890',
            'email': 'john.driver@example.com',
            'status': 'active',
            'on_duty': True,
        },
        {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '+1987654321',
            'email': 'jane.smith@example.com',
            'status': 'active',
            'on_duty': False,
        },
    ]
    
    drivers = []
    for driver_data in drivers_data:
        driver, created = FleetDriver.objects.get_or_create(
            email=driver_data['email'],
            defaults={
                'id': uuid.uuid4(),
                'fleet_id': uuid.uuid4(),
                **driver_data
            }
        )
        drivers.append(driver)
        print(f"{'Created' if created else 'Found'} driver: {driver.first_name} {driver.last_name}")
    
    # Create trucks
    trucks_data = [
        {
            'truck_identifier': 'trk2',
            'plate': 'ZWE-1001',
            'vin': 'VIN123456789',
            'make': 'Volvo',
            'model': 'FH16',
            'year': 2020,
            'fuel_capacity_liters': 500,
            'status': 'idle',
            'is_moving': False,
            'last_latitude': -17.8252,
            'last_longitude': 31.0335,
        },
        {
            'truck_identifier': 'trk3',
            'plate': 'ATY 3272',
            'vin': 'VIN987654321',
            'make': 'Mercedes',
            'model': 'Actros',
            'year': 2021,
            'fuel_capacity_liters': 600,
            'status': 'enroute',
            'is_moving': True,
            'last_latitude': -17.8256,
            'last_longitude': 31.0345,
        },
        {
            'truck_identifier': 'trk4',
            'plate': 'AQW7645',
            'vin': 'VIN111222333',
            'make': 'Hino',
            'model': '500',
            'year': 2019,
            'fuel_capacity_liters': 400,
            'status': 'idle',
            'is_moving': False,
            'last_latitude': -17.8260,
            'last_longitude': 31.0340,
        },
        {
            'truck_identifier': 'TRK1',
            'plate': 'AXE5422',
            'vin': 'VIN444555666',
            'make': 'Scania',
            'model': 'R500',
            'year': 2022,
            'fuel_capacity_liters': 550,
            'status': 'idle',
            'is_moving': False,
            'last_latitude': -17.8250,
            'last_longitude': 31.0330,
        },
    ]
    
    trucks = []
    for i, truck_data in enumerate(trucks_data):
        truck, created = FleetTruck.objects.get_or_create(
            plate=truck_data['plate'],
            defaults={
                'id': uuid.uuid4(),
                'fleet_id': uuid.uuid4(),
                'assigned_driver': drivers[i % len(drivers)] if drivers else None,
                **truck_data
            }
        )
        trucks.append(truck)
        print(f"{'Created' if created else 'Found'} truck: {truck.truck_identifier} ({truck.plate})")
    
    # Create a mission
    if drivers and trucks:
        mission, created = FleetMission.objects.get_or_create(
            mission_number='MIS001',
            defaults={
                'id': uuid.uuid4(),
                'fleet_id': trucks[1].fleet_id,
                'driver_id': drivers[0].id,
                'truck_id': trucks[1].id,
                'origin': 'Harare',
                'destination': 'Bulawayo',
                'status': 'in_progress',
                'mission_date': datetime.now().date(),
            }
        )
        print(f"{'Created' if created else 'Found'} mission: {mission.mission_number}")
    
    print("\n✅ Database seeding complete!")

if __name__ == '__main__':
    try:
        seed_fleet_data()
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
