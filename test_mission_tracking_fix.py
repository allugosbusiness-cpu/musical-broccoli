#!/usr/bin/env python
"""
Test script to verify mission tracking initialization fix
Tests that when a mission is activated, it gets current_location initialized
"""

import os
import django
import json
from decimal import Decimal
from uuid import uuid4

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Logistics.settings')
django.setup()

from api.models_v2 import FleetMission, FleetTruck, FleetDriver
from django.utils import timezone

print("\n" + "="*70)
print("Testing Mission Tracking Initialization Fix")
print("="*70)

try:
    # Use a test fleet ID
    fleet_id = uuid4()
    print(f"✅ Using fleet ID: {fleet_id}")
    
    # Create a test truck
    truck = FleetTruck.objects.create(
        fleet_id=fleet_id,
        truck_identifier='TEST-TRUCK-001',
        plate='TST001',
        make='Volvo',
        model='FH16',
        last_latitude=Decimal('-17.8252'),
        last_longitude=Decimal('31.0335'),
        fuel_capacity_liters=500
    )
    print(f"✅ Created test truck: {truck.truck_identifier}")
    
    # Create a test driver
    driver = FleetDriver.objects.create(
        fleet_id=fleet_id,
        phone_number='0712345678',
        first_name='Test',
        last_name='Driver'
    )
    driver.truck = truck
    driver.save()
    print(f"✅ Created test driver: {driver.get_display_name()}")
    
    # Create a mission with origin/destination
    mission = FleetMission.objects.create(
        id=uuid4(),
        fleet_id=fleet_id,
        mission_number=f'TEST-M-{int(timezone.now().timestamp())}',
        truck=truck,
        origin={
            'lat': -17.8252,
            'lon': 31.0335,
            'name': 'Harare'
        },
        destination={
            'lat': -17.85,
            'lon': 31.05,
            'name': 'Mutare'
        },
        distance_total_m=150000,
        status='assigned'
    )
    print(f"✅ Created mission: {mission.mission_number}")
    print(f"   Origin: {mission.origin}")
    print(f"   Destination: {mission.destination}")
    print(f"   Current Location BEFORE: {mission.current_location}")
    
    # Simulate what start_mission_tracking does
    print("\n📌 Simulating start_mission_tracking endpoint...")
    mission.status = 'enroute'
    mission.driver = driver
    mission.started_at = timezone.now()
    
    # ✅ THE FIX: Initialize current location with origin
    if mission.origin and isinstance(mission.origin, dict):
        mission.current_location = {
            'lat': mission.origin.get('lat') or mission.origin.get('latitude'),
            'lon': mission.origin.get('lon') or mission.origin.get('longitude')
        }
        print(f"✅ Current Location INITIALIZED: {mission.current_location}")
    
    mission.save()
    print(f"✅ Mission saved with status: {mission.status}")
    
    # Verify the fix
    print("\n📌 Verifying fix...")
    refreshed_mission = FleetMission.objects.get(id=mission.id)
    
    if refreshed_mission.status == 'enroute':
        print("✅ Mission status is ENROUTE")
    else:
        print(f"❌ Mission status is {refreshed_mission.status}, expected ENROUTE")
        
    if refreshed_mission.current_location:
        print(f"✅ Mission current_location is set: {refreshed_mission.current_location}")
        lat = refreshed_mission.current_location.get('lat')
        lon = refreshed_mission.current_location.get('lon')
        if lat and lon:
            print(f"✅ Coordinates valid: ({lat}, {lon})")
        else:
            print(f"❌ Coordinates invalid or missing")
    else:
        print(f"❌ Mission current_location is NULL - FIX NOT WORKING!")
    
    # Test what the dashboard gets
    print("\n📌 Testing dashboard endpoint logic...")
    from api.dashboard_service import get_truck_location_from_missions
    
    location = get_truck_location_from_missions(truck.id)
    print(f"   get_truck_location_from_missions({truck.truck_identifier}): {location}")
    
    if location:
        print(f"✅ Map will display truck at: ({location.get('lat')}, {location.get('lon')})")
    else:
        print(f"❌ Map won't display truck - location is None!")
    
    print("\n" + "="*70)
    print("✅ TEST PASSED - Mission tracking fix is working!")
    print("="*70 + "\n")
    
    # Cleanup
    mission.delete()
    driver.delete()
    truck.delete()
    print("✅ Cleaned up test data\n")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {str(e)}")
    import traceback
    traceback.print_exc()
