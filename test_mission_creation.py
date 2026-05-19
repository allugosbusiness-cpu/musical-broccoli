#!/usr/bin/env python
"""
Test script to simulate mission creation through API like the form does
"""
import os
import sys
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.Logistics.settings')
sys.path.insert(0, 'server')
django.setup()

from django.test import Client
from server.api.models import FleetDriver, FleetTruck

print("=" * 70)
print("TEST: Mission Creation via API")
print("=" * 70)

# Get a truck and driver from database
print("\n1. FINDING TRUCK & DRIVER:")
print("-" * 70)
trucks = FleetTruck.objects.all()[:1]
drivers = FleetDriver.objects.all()[:1]

if not trucks or not drivers:
    print("No trucks or drivers found! Creating test data...")
    from uuid import uuid4
    truck = FleetTruck.objects.create(
        truck_identifier="TEST-TRUCK-001",
        plate="TEST-PLT-001",
        vin="VIN-TEST-001"
    )
    driver = FleetDriver.objects.create(
        first_name="Test",
        last_name="Driver",
        email="test@example.com",
        phone_number="555-0001"
    )
    print(f"Created truck: {truck.id} - {truck.truck_identifier}")
    print(f"Created driver: {driver.id} - {driver.first_name} {driver.last_name}")
else:
    truck = trucks[0]
    driver = drivers[0]
    print(f"Using truck: {truck.id} - {truck.truck_identifier}")
    print(f"Using driver: {driver.id} - {driver.first_name} {driver.last_name}")

# Create mission via API (as form would)
print("\n2. POSTING MISSION TO API:")
print("-" * 70)
client = Client()

mission_payload = {
    "mission_number": f"API-TEST-{str(truck.id)[:8]}",
    "truck": str(truck.id),  # Send as UUID string
    "driver": str(driver.id),  # Send as UUID string
    "status": "planned",
    "origin": {
        "name": "Test Origin",
        "lat": -1.2921,
        "lng": 36.8219,
    },
    "destination": {
        "name": "Test Destination",
        "lat": -1.2850,
        "lng": 36.8270,
    },
    "priority": "normal",
}

print(f"Payload:\n{json.dumps(mission_payload, indent=2)}")

response = client.post(
    '/api/v1/missions/',
    data=json.dumps(mission_payload),
    content_type='application/json'
)

print(f"\nResponse Status: {response.status_code}")

if response.status_code in [200, 201]:
    try:
        created_mission = json.loads(response.content)
        print(f"\nCREATED MISSION:")
        print(f"  mission_number: {created_mission.get('mission_number')}")
        print(f"  truck (ID): {created_mission.get('truck')}")
        print(f"  truck_name: {created_mission.get('truck_name')}")
        print(f"  driver (ID): {created_mission.get('driver')}")
        print(f"  driver_name: {created_mission.get('driver_name')}")
        print(f"  distance_total_m: {created_mission.get('distance_total_m')}")
        print(f"  origin: {created_mission.get('origin')}")
        print(f"  destination: {created_mission.get('destination')}")
        
        # Verify by querying the mission back
        print("\n3. VERIFY: Fetch mission back from database:")
        print("-" * 70)
        response2 = client.get(f'/api/v1/missions/{created_mission.get("id")}/')
        if response2.status_code == 200:
            fetched = json.loads(response2.content)
            print(f"  truck_name: {fetched.get('truck_name')}")
            print(f"  driver_name: {fetched.get('driver_name')}")
            print(f"  distance_total_m: {fetched.get('distance_total_m')}")
        else:
            print(f"Error fetching: {response2.status_code}")
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response: {response.content}")
else:
    print(f"ERROR: {response.status_code}")
    print(f"Response: {response.content.decode('utf-8', errors='ignore')}")

print("\n" + "=" * 70)
