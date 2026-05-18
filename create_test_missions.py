#!/usr/bin/env python
"""Create test driver and missions for mobile app testing"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server'))
django.setup()

from api.models import FleetDriver, FleetTruck, FleetMission

def create_test_data():
    """Create test driver, truck, and missions"""
    
    # Create or get a test truck
    try:
        truck = FleetTruck.objects.first()
        if not truck:
            truck = FleetTruck.objects.create(
                truck_identifier="TEST-TRUCK-001",
                plate="TST123",
                status="idle",
                last_latitude=Decimal("-17.8252"),
                last_longitude=Decimal("31.0335"),
                odometer_km=Decimal("0"),
                fuel_consumed_liters=Decimal("0")
            )
            print(f"? Created test truck: {truck.truck_identifier}")
        else:
            print(f"? Found existing truck: {truck.truck_identifier}")
    except Exception as e:
        print(f"? Error with truck: {e}")
        return
    
    # Create or get a test driver
    try:
        driver, created = FleetDriver.objects.get_or_create(
            phone_number="+2671234567",
            defaults={
                'first_name': 'Test',
                'last_name': 'Driver',
                'status': 'active',
                'truck': truck,
                'latitude': Decimal("-17.8252"),
                'longitude': Decimal("31.0335")
            }
        )
        if created:
            print(f"? Created test driver: {driver.first_name} {driver.last_name}")
            print(f"   Driver ID: {driver.id}")
            print(f"   Phone: {driver.phone_number}")
        else:
            print(f"? Found existing driver: {driver.first_name} {driver.last_name}")
            print(f"   Driver ID: {driver.id}")
    except Exception as e:
        print(f"? Error creating driver: {e}")
        return
    
    # Create test missions
    missions_data = [
        {
            'mission_number': 'MISSION-TEST-001',
            'origin': {'lat': -17.8252, 'lon': 31.0335, 'address': 'Harare Central'},
            'destination': {'lat': -17.8500, 'lon': 31.0500, 'address': 'Eastlea'},
            'priority': 'normal',
            'cargo': {'items': ['Package 1', 'Package 2'], 'weight': '25kg'}
        },
        {
            'mission_number': 'MISSION-TEST-002',
            'origin': {'lat': -17.8252, 'lon': 31.0335, 'address': 'Harare Central'},
            'destination': {'lat': -17.7800, 'lon': 31.0800, 'address': 'Southlea'},
            'priority': 'high',
            'cargo': {'items': ['Urgent Delivery'], 'weight': '10kg'}
        },
        {
            'mission_number': 'MISSION-TEST-003',
            'origin': {'lat': -17.8252, 'lon': 31.0335, 'address': 'Harare Central'},
            'destination': {'lat': -17.9000, 'lon': 31.0000, 'address': 'Avondale'},
            'priority': 'normal',
            'cargo': {'items': ['Regular Shipment'], 'weight': '50kg'}
        }
    ]
    
    print(f"\n?? Creating test missions for driver {driver.id}...")
    for mission_data in missions_data:
        try:
            mission, created = FleetMission.objects.get_or_create(
                mission_number=mission_data['mission_number'],
                defaults={
                    'driver': driver,
                    'truck': truck,
                    'status': 'assigned',
                    'origin': mission_data['origin'],
                    'destination': mission_data['destination'],
                    'priority': mission_data['priority'],
                    'cargo': mission_data['cargo'],
                    'distance_total_m': Decimal('5000')
                }
            )
            if created:
                print(f"? Created mission: {mission.mission_number}")
            else:
                print(f"??  Mission already exists: {mission.mission_number}")
        except Exception as e:
            print(f"? Error creating mission {mission_data['mission_number']}: {e}")
    
    print(f"\n? Test data setup complete!")
    print(f"Driver {driver.first_name} ({driver.id}) now has {driver.missions.count()} missions available")
    print(f"\n?? Test endpoint: https://pulsetrack-back.onrender.com/api/v1/mobile/driver/{driver.id}/available-missions/")

if __name__ == "__main__":
    create_test_data()

